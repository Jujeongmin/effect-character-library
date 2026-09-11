# -*- coding: utf-8 -*-
"""Turn a baked-in flat background into real transparency.

Some sheets were exported onto black (or, for 260114_spark, a dark teal) rather
than onto alpha, so drawing them normally paints a rectangle over the game. The
`blend: "lighter"` hint hides that only where the engine composites additively -
every other use still shows the box.

These are additive glows, so the fix is exact: take the flat backdrop colour,
subtract it, and let what is left of the brightness become alpha. A pixel as
dark as the backdrop turns fully transparent, a bright core stays fully opaque,
and RGB is untouched so the glow keeps its colour.

    python tools/dekey.py                      # every sheet still flagged opaque
    python tools/dekey.py spark_5 ring         # just these
    python tools/dekey.py --dry-run            # report without rewriting
"""
import json
import os
import sys

from PIL import Image, ImageChops

Image.MAX_IMAGE_PIXELS = None


def default_library(root):
    """web/ while building, the package root once it has been shipped."""
    return root if os.path.exists(os.path.join(root, 'effects.json')) \
        else os.path.join(root, 'web')


def backdrop_level(img):
    """Brightness of the most common colour - the flat backdrop."""
    counts = img.convert('RGB').getcolors(maxcolors=1 << 24)
    if not counts:
        return 0
    _, colour = max(counts)
    return max(colour)


def brightness(r, g, b):
    """Per-pixel max of the three channels."""
    return ImageChops.lighter(ImageChops.lighter(r, g), b)


def dekey(path, dry_run=False):
    """Key the backdrop out of one sheet. Returns (level, newly transparent px)."""
    img = Image.open(path).convert('RGBA')
    r, g, b, a = img.split()
    level = backdrop_level(img)
    span = 255 - level
    if span <= 0:
        return level, 0

    keyed = brightness(r, g, b).point(
        lambda v: 0 if v <= level else min(255, round((v - level) * 255 / span)))
    # A pixel that was already transparent must stay transparent.
    out_a = ImageChops.multiply(keyed, a)

    gained = sum(out_a.histogram()[:1]) - sum(a.histogram()[:1])
    if not dry_run:
        Image.merge('RGBA', (r, g, b, out_a)).save(path, optimize=True)
    return level, gained


def main(lib_dir, ids, dry_run):
    manifest_path = os.path.join(lib_dir, 'effects.json')
    with open(manifest_path, encoding='utf-8') as f:
        manifest = json.load(f)

    targets = [e for e in manifest['assets']
               if (e['id'] in ids if ids else e.get('opaque'))]
    if not targets:
        print('nothing to do')
        return

    for e in targets:
        level, gained = dekey(os.path.join(lib_dir, e['file']), dry_run)
        print('%-16s backdrop %3d -> %d px newly transparent%s'
              % (e['id'], level, gained, ' [dry run]' if dry_run else ''))
        if not dry_run:
            e['opaque'] = False
            e.pop('blend', None)
            e['note'] = 'backdrop keyed out of the original opaque export'

    if not dry_run:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lib = args[0] if args and os.path.isdir(args[0]) else default_library(root)
    wanted = {a for a in args if not os.path.isdir(a)}
    main(lib, wanted, '--dry-run' in sys.argv)

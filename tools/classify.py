# -*- coding: utf-8 -*-
"""Second pass over a built library: split reference material out of the assets.

The raw folders mix real sprites with a lot of material that merely *looks*
like one after conversion:

  * in-game screen recordings   - GIFs of the whole game screen, UI and all
  * third-party reference clips - downloaded from VFX sites, some watermarked
  * contact sheets / mockups    - one huge PNG showing many variants at once
  * duplicate _preview renders  - opaque copies of a sprite that already exists

All of that is moved to reference/ and flagged `reference: true`. Because the
exploded spritesheet of a 300-frame screen recording is both useless and
enormous, the PNG is dropped and the original source file is copied in instead.

Assets exported on black rather than on alpha are flagged `opaque` and given a
`blend: "lighter"` hint - additive blending drops the black background.

Idempotent - safe to re-run against an already-classified build:

    python tools/classify.py [web_dir]
"""
import json
import os
import re
import shutil
import sys

from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # our own sheets, not untrusted uploads

MAX_TEXTURE = 4096          # single-texture cap on many mobile GPUs
CAPTURE_MIN_W = 480         # a "frame" this large is a screen, not a sprite
CAPTURE_MIN_H = 320
CAPTURE_MIN_FRAMES = 8
MOCKUP_MIN_SIDE = 2000      # single still this big is a contact sheet

REFERENCE_MARKERS = ('ingame', 'palette_compare', 'skill_style')
PREVIEW_RE = re.compile(r'_preview(_\d+)?$')
OLD_RE = re.compile(r'_old(_\d+)?$')
REF_DIR_RE = re.compile(r'(^|/)00_reference/', re.I)
KINDS = ('effects', 'textures', 'reference')
SOURCE_ROOTS = {
    '06_effect': '_raw_06',
    'effect_old': '_raw_old',
    '012_effect': '_raw_012',
    'unity': '_unpacked',
}


def is_opaque(path):
    """True when no pixel in the sheet is even partially transparent."""
    try:
        alpha = Image.open(path).convert('RGBA').getchannel('A')
    except Exception:
        return False
    return alpha.getextrema()[0] == 255


def base_id(asset_id):
    """Strip a _preview / _old marker and any numeric dedupe suffix."""
    s = PREVIEW_RE.sub('', asset_id)
    s = OLD_RE.sub('', s)
    return re.sub(r'_\d+$', '', s)


def locate(web_dir, entry):
    """Find the entry's PNG wherever a previous run left it."""
    name = os.path.basename(entry['file'])
    for kind in KINDS:
        p = os.path.join(web_dir, kind, name)
        if os.path.exists(p):
            return kind, p
    return None, None


def source_path(root, entry):
    """Absolute path of the original file this entry was built from."""
    src = entry.get('source')   # absent in the published library manifest
    if not src:
        return None
    tag, _, rel = src.partition('/')
    base = SOURCE_ROOTS.get(tag)
    if not base:
        return None
    p = os.path.join(root, base, rel.replace('/', os.sep))
    return p if os.path.exists(p) else None


def reference_reason(entry, real_bases):
    """Why this entry is documentation rather than a shippable sprite, or None.

    'Opaque and large' is deliberately NOT a signal on its own - plenty of real
    effects (auras, backgrounds) were exported on black at full size.
    """
    aid = entry['id']
    src = entry.get('source', '')   # absent in the published library manifest
    ext = src.rsplit('.', 1)[-1].lower() if '.' in src else ''

    if src and REF_DIR_RE.search(src):
        return 'sits in a 00_reference folder (third-party / gathered clips)'
    for marker in REFERENCE_MARKERS:
        if marker in aid:
            return 'in-game capture or comparison sheet'
    if OLD_RE.search(aid):
        return 'superseded _old export'
    if PREVIEW_RE.search(aid) and base_id(aid) in real_bases:
        return 'preview render of ' + base_id(aid)
    if ext == 'gif' and entry['frames'] >= CAPTURE_MIN_FRAMES \
            and entry['frameWidth'] >= CAPTURE_MIN_W \
            and entry['frameHeight'] >= CAPTURE_MIN_H:
        return 'screen-sized GIF recording (%dx%d, %d frames)' % (
            entry['frameWidth'], entry['frameHeight'], entry['frames'])
    if entry['frames'] == 1 and (entry['width'] >= MOCKUP_MIN_SIDE
                                 or entry['height'] >= MOCKUP_MIN_SIDE):
        return 'oversized single still - contact sheet or mockup'
    return None


def classify(web_dir):
    root = os.path.dirname(os.path.abspath(web_dir.rstrip(os.sep)))
    manifest_path = os.path.join(web_dir, 'effects.json')
    with open(manifest_path, encoding='utf-8') as f:
        manifest = json.load(f)
    assets = manifest['assets']

    for kind in KINDS:
        os.makedirs(os.path.join(web_dir, kind), exist_ok=True)

    real_bases = set()
    for e in assets:
        if not PREVIEW_RE.search(e['id']) and not OLD_RE.search(e['id']):
            real_bases.add(base_id(e['id']))

    freed, missing = 0, []
    for e in assets:
        cur_kind, cur_path = locate(web_dir, e)
        reason = reference_reason(e, real_bases)

        if reason:
            e['reference'] = True
            e['referenceReason'] = reason
            # Keep the original file, drop the exploded sheet - for a 300-frame
            # screen recording the sheet is hundreds of MB and of no use.
            orig = source_path(root, e)
            if orig:
                dst = os.path.join(web_dir, 'reference',
                                   e['id'] + os.path.splitext(orig)[1].lower())
                same = cur_path and os.path.abspath(cur_path) == os.path.abspath(dst)
                if not os.path.exists(dst) or same:
                    shutil.copy2(orig, dst)
                # Only drop the exploded sheet when it is a different file -
                # when the original is a .png the two paths collide.
                if cur_path and not same and os.path.exists(cur_path):
                    freed += os.path.getsize(cur_path)
                    os.remove(cur_path)
                e['file'] = 'reference/' + os.path.basename(dst)
                e['originalOnly'] = True
            elif cur_path:
                dst = os.path.join(web_dir, 'reference', os.path.basename(cur_path))
                if cur_path != dst:
                    os.replace(cur_path, dst)
                e['file'] = 'reference/' + os.path.basename(dst)
            continue

        e['reference'] = False
        e.pop('referenceReason', None)
        e.pop('originalOnly', None)
        if cur_path is None:
            missing.append(e['id'])
            continue

        e['opaque'] = is_opaque(cur_path)
        if e['opaque']:
            e['blend'] = 'lighter'
        else:
            e.pop('blend', None)
        if e['width'] > MAX_TEXTURE or e['height'] > MAX_TEXTURE:
            e['oversized'] = True
        else:
            e.pop('oversized', None)

        want = 'effects' if e['frames'] > 1 else 'textures'
        if cur_kind != want:
            os.replace(cur_path, os.path.join(web_dir, want, os.path.basename(cur_path)))
        e['file'] = '%s/%s' % (want, os.path.basename(cur_path))

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    usable = [e for e in assets if not e['reference']]
    refs = [e for e in assets if e['reference']]
    over = [e for e in usable if e.get('oversized')]
    print('total %d | usable %d | reference %d | opaque %d | oversized(usable) %d'
          % (len(assets), len(usable), len(refs),
             sum(1 for e in usable if e.get('opaque')), len(over)))
    print('reclaimed %.1f MB of exploded reference sheets' % (freed / 1e6))
    from collections import Counter
    for reason, n in Counter(e['referenceReason'].split('(')[0].strip()
                             for e in refs).most_common():
        print('  ref  %-4d %s' % (n, reason))
    for e in over:
        print('  big  %-42s %dx%d' % (e['id'], e['width'], e['height']))
    if missing:
        print('  MISSING FILE for %d entries: %s' % (len(missing), ', '.join(missing[:10])))


def default_library(root):
    """web/ while building, the package root once it has been shipped."""
    return root if os.path.exists(os.path.join(root, 'effects.json'))         else os.path.join(root, 'web')


if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    classify(sys.argv[1] if len(sys.argv) > 1 else default_library(root))

# -*- coding: utf-8 -*-
"""Add the Unity particle textures to the library as single-image assets.

These are the pieces a particle system emits - glows, rays, magic circles,
smoke puffs, sparkles. On their own they do not animate, but a game can scale,
spin and fade them, so they are effect material even though they are one frame.

What is filtered out: anything that is game art rather than VFX material -
character parts, backgrounds, UI atlases - plus the status icons and HUD words
(+HP, -Attack, VICTORY, LEVEL UP), which carry baked-in text.

    python tools/add_textures.py <staging_dir> <library_dir> [--dry-run]
"""
import hashlib
import json
import os
import re
import sys

from PIL import Image

# Only these parts of the Unity trees hold particle material.
VFX_DIRS = ('00_Materials', 'VFX/MaterialsTextures', 'VFX/Prefabs')

# Names that are UI or status art, not particle material.
DROP_PATTERNS = (
    r'^ny_buff_',        # +HP / -Attack / Bleed ... status icons, text baked in
    r'^ny_result_',      # GOOD / GREAT / PERFECT
    r'^ny_menu_',
    r'^ny_ui_',
    r'^ui_',
    r'^ny_levelup$',
    r'^ny_victory$',
    r'^aura_0\d_',       # colour-variant atlases, several pieces per image
)


def is_texture(entry):
    # The grid guess is meaningless here: a particle system samples the whole
    # texture, so a "2 frame" reading of two shapes side by side is noise.
    if not any(d in entry['source'] for d in VFX_DIRS):
        return False
    return not any(re.search(p, entry['id']) for p in DROP_PATTERNS)


def digest(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def main(staging, library, dry_run=False):
    with open(os.path.join(staging, 'effects.json'), encoding='utf-8') as f:
        incoming = json.load(f)['assets']
    lib_path = os.path.join(library, 'effects.json')
    with open(lib_path, encoding='utf-8') as f:
        manifest = json.load(f)

    taken_ids = {e['id'] for e in manifest['assets']}
    taken_hashes = {digest(os.path.join(library, e['file'])) for e in manifest['assets']}

    out_dir = os.path.join(library, 'singles')
    if not dry_run:
        os.makedirs(out_dir, exist_ok=True)

    added, skipped_dup = [], 0
    for e in sorted(incoming, key=lambda x: x['id']):
        if not is_texture(e):
            continue
        src = os.path.join(staging, e['file'])
        if digest(src) in taken_hashes:
            skipped_dup += 1
            continue

        uid, n = e['id'], 1
        while uid in taken_ids:
            n += 1
            uid = '%s_%d' % (e['id'], n)
        taken_ids.add(uid)

        rel = 'singles/%s.webp' % uid
        if not dry_run:
            Image.open(src).save(os.path.join(library, rel), lossless=True, exact=True)
        manifest['assets'].append({
            'id': uid, 'category': 'single', 'file': rel,
            'width': e['width'], 'height': e['height'],
            'frameWidth': e['width'], 'frameHeight': e['height'],
            'frames': 1, 'cols': 1, 'rows': 1,
            'opaque': bool(e.get('opaque')),
        })
        added.append(uid)

    manifest['assets'].sort(key=lambda x: (x['category'], x['id']))
    # The library is published: never ship internal studio paths. Staging keeps
    # `source` (is_texture reads it above); the library manifest does not.
    for a in manifest['assets']:
        a.pop('source', None)
    if not dry_run:
        with open(lib_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    print('%sadded %d textures (%d already in the library)'
          % ('[dry run] ' if dry_run else '', len(added), skipped_dup))
    print('library now holds %d assets' % len(manifest['assets']))
    for i in range(0, len(added), 6):
        print('  ' + '  '.join('%-22s' % a for a in added[i:i + 6]))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    main(args[0], args[1], '--dry-run' in sys.argv)

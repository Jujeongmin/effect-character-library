# -*- coding: utf-8 -*-
"""Drop everything in the library that is not effect material.

Game art rather than VFX - concept art, weapon parts, character pieces, UI and
reward screens - goes, and so does each asset listed in DROP_IDS, all of which
were checked frame by frame. Single images stay: the Unity particle textures
are what a particle system emits, so they are material even though they do not
animate on their own.

Generated files only - the raw folders (_raw_*, _unpacked) are untouched, so
`build.py` + `classify.py` regenerates everything this removes.

    python tools/prune.py [web_dir] [--dry-run]
"""
import json
import os
import shutil
import sys

# Categories that are game art rather than combat VFX.
DROP_CATEGORIES = {
    'ui', 'aura_ui', 'background', 'weapon', 'pet',
    'idle_reward', 'content_unlock', 'season_pass', 'adventure_boss',
}

# Checked frame by frame: these animate, and sit in an effect category, but are
# not effects. Screen recordings under the capture size threshold, blank
# working files, character art and icons.
DROP_IDS = {
    'aura_arena_white': 'in-game footage of a character in the forest map',
    'aura_event_white_03': 'in-game footage of a character in the forest map',
    'aura_aegis_bombard_jakeolpail': 'character-select screen capture',
    'hateu': 'quest-reward screen capture',
    'emotion_heart_01': 'character illustration, not an effect',
    'hwatgeup_aura': 'blank grey working file',
    'eoleup_aura_01': 'blank white working file',
    'eoleup_aura_keolreobari': 'blank white working file',
    '8woldeuipekteu_focus_debuff_hoepiyul': 'blank white working file',
    'skill_icon_2': 'shield icon, not an effect',
    'eoleup_pet_f_2': 'pet character sprite, not an effect',
    'group_6': 'stray Figma slice, not an effect',
    'aura_ice_transcendent_2': 'grey backdrop baked into every frame',
    'poison_1': 'mockup: effect composited over a monster sprite',
    'ring_01': 'mockup: effect composited over a monster sprite',
    'spark_2': 'mockup: effect composited over a monster sprite',
    'poison_8': 'mockup: effect composited over a monster sprite',
    # Texture atlases of unrelated pieces that the grid guess read as frames.
    'aura_01_cyan': 'atlas of unrelated aura parts, not an animation',
    'aura_01_cyan_2': 'atlas of unrelated aura parts, not an animation',
    'ny_feather_02_png': 'two unrelated particle textures in one image',
    'ny_glow_wind': '16px grey particle atom, nothing to animate',
    # One long sprite sliced into thirds by the guessed pitch.
    'thor_projectile_02': 'single streak cut into 3 by a wrong grid',
    'thor_projectile_03': 'single streak cut into 3 by a wrong grid',
    'lightning_3': 'PSD layers misaligned - half the frames are black bars',
    'aura_ice_transcendent': 'two unrelated pieces side by side, not an animation',
    'projectile': 'PSD layers came out near-empty at 400x300',
    'thor_projectile_01': '8x50 specks, nothing usable',
    'thor_projectile_04': '8x50 specks, nothing usable',
    # "RTFX generator" trial watermark tiled across every frame - not ours.
    'spark_5': 'third-party RTFX generator watermark baked in',
    # Same picture as thor_thunder, but a JPG with the alpha flattened away.
    'thor_thunder2': 'JPG duplicate of thor_thunder, no alpha',
    'ny_boss': 'BOSS banner artwork with text, not an effect',
    'ny_00': '4x4 canvas with no opaque pixels at all - an empty file',
    # Same 16-frame sequence as bomb_drop_2_3, but squeezed into 64px cells
    # that crop the flash and the smoke.
    'bomb_drop_1_3': 'cropped 64px copy of bomb_drop_2_3',
}

# Concept art folders - the drawings an effect was designed from.
CONCEPT_MARKER = '원화'


def keep(entry):
    if entry.get('reference'):
        return False
    if entry['category'] in DROP_CATEGORIES:
        return False
    if entry['id'] in DROP_IDS:
        return False
    # `source` is stripped from the published manifest (see below).
    return CONCEPT_MARKER not in entry.get('source', '')


def prune(web_dir, dry_run=False):
    manifest_path = os.path.join(web_dir, 'effects.json')
    with open(manifest_path, encoding='utf-8') as f:
        manifest = json.load(f)
    assets = manifest['assets']

    kept = [e for e in assets if keep(e)]
    dropped = [e for e in assets if not keep(e)]

    freed = 0
    for e in dropped:
        p = os.path.join(web_dir, e['file'])
        if os.path.exists(p):
            freed += os.path.getsize(p)
            if not dry_run:
                os.remove(p)

    ref_dir = os.path.join(web_dir, 'reference')
    ref_size = 0
    if os.path.isdir(ref_dir):
        for dirpath, _, names in os.walk(ref_dir):
            for n in names:
                ref_size += os.path.getsize(os.path.join(dirpath, n))
        if not dry_run:
            shutil.rmtree(ref_dir)

    from collections import Counter
    by_cat = Counter(e['category'] for e in kept)

    if not dry_run:
        # Last pass before the library ships: drop internal studio paths.
        for e in kept:
            e.pop('source', None)
        manifest['assets'] = kept
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        # textures/ only ever held stills, so it is empty now.
        tex = os.path.join(web_dir, 'textures')
        if os.path.isdir(tex) and not os.listdir(tex):
            os.rmdir(tex)

    print('%skept %d effects, dropped %d entries' %
          ('[dry run] ' if dry_run else '', len(kept), len(dropped)))
    print('freed %.1f MB of dropped sheets + %.1f MB of reference originals'
          % (freed / 1e6, ref_size / 1e6))
    for cat, n in by_cat.most_common():
        print('  %-16s %d' % (cat, n))


def default_library(root):
    """web/ while building, the package root once it has been shipped."""
    return root if os.path.exists(os.path.join(root, 'effects.json'))         else os.path.join(root, 'web')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--dry-run']
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prune(args[0] if args else default_library(root),
          dry_run='--dry-run' in sys.argv)

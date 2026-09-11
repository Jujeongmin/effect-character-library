# -*- coding: utf-8 -*-
"""Verify (and fix) each sheet's frame grid against the pixels.

build.py guesses a grid from the filename, falling back to "one side is a whole
multiple of the other". Both guesses go wrong the same way: a sheet gets cut on
the wrong pitch, so sprites are sliced in half, or several sprites land in one
frame.

A grid is right when two things hold:

  * no cell boundary crosses content - otherwise a sprite is cut in half
  * no cell is empty            - otherwise the sheet was split too finely

So for each axis this tries every divisor of the sheet size and keeps the
finest split satisfying both. That is measurement, not inference: a sheet whose
frames touch has no valid split above 1 and is left exactly as the manifest has
it.

    python tools/regrid.py [web_dir]            # report only
    python tools/regrid.py [web_dir] --apply    # rewrite effects.json
"""
import json
import os
import sys

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

# Unity particle materials pack their frames as a block inside each cell, so
# the "one side is a multiple of the other" guess under-splits them: every
# displayed frame holds a 2x2 or 4x2 grid of the real ones. Checked by eye.
GRID_OVERRIDES = {
    'ny_electric_02_sprite': (8, 2),
    'ny_attack_02': (4, 2),
    'ny_attack_04_sprite': (4, 2),
    'ny_flash_05_sprite': (4, 2),
    'ny_lines_01': (4, 2),
}

# Unity flipbooks that arrived looking like one still image - the grid was
# measured from the alpha gutters and then checked frame by frame. Promoting
# them moves the file out of textures/ and gives them a real category.
PROMOTIONS = {
    'ny_electric_01_sprite': (4, 4, 'lightning'),
    'ny_electric_03_sprite': (2, 2, 'lightning'),
    'ny_smoke_04_fire_sprite': (8, 8, 'misc'),
    'ny_smoke_fire_sprite': (2, 2, 'misc'),
    'ny_sprites_blood': (2, 4, 'impact'),
    'ny_attack_05_fire': (4, 4, 'misc'),
    'ny_attack_06_sprite': (8, 5, 'impact'),
    'ny_attack_10_sprite': (10, 1, 'impact'),
    'ny_explosion_01': (2, 2, 'explosion'),
}

# Some of those sheets stack two colour variants of the same 4-frame animation,
# one per row. Playing straight through makes the effect change colour halfway,
# so only the first row is played; the rest of the sheet stays in the PNG.
FRAME_LIMITS = {
    'ny_attack_02': (4, 'row 2 is the same animation in orange'),
    'ny_attack_04_sprite': (4, 'row 2 is a second slash variant'),
    'ny_flash_05_sprite': (4, 'row 2 is a second arc variant'),
    'ny_lines_01': (4, 'row 2 is a second streak variant'),
}

ALPHA_FLOOR = 8    # below this a pixel counts as empty
MIN_FRAME = 8      # never split finer than this
CUT_FRACTION = 0.04    # boundary energy above this share of the peak = a real cut
EMPTY_FRACTION = 0.002 # cell holding less than this share of the sheet = blank


def energy(img):
    """(per-column, per-row) summed alpha - how much sprite sits on that line."""
    alpha = img.getchannel('A')
    w, h = img.size
    px = alpha.load()
    cols = [0] * w
    rows = [0] * h
    for y in range(h):
        for x in range(w):
            a = px[x, y]
            if a >= ALPHA_FLOOR:
                cols[x] += a
                rows[y] += a
    return cols, rows


def divisors(n):
    return [d for d in range(1, n + 1) if n % d == 0]


def faults(energies, n):
    """(cuts, empties) from splitting this axis into n cells.

    A boundary only counts as a cut when real sprite body crosses it - a glow
    halo bleeding a few faint pixels past the edge is normal and ignored.
    """
    total = len(energies)
    size = total // n
    peak = max(energies) or 1
    cut_level = peak * CUT_FRACTION
    body = sum(energies)
    cuts = empties = 0
    for i in range(n):
        lo, hi = i * size, (i + 1) * size
        if sum(energies[lo:hi]) <= body * EMPTY_FRACTION:
            empties += 1
        if i and min(energies[lo - 1], energies[lo]) > cut_level:
            cuts += 1
    return cuts, empties


def best_split(energies):
    """Finest split of this axis that cuts nothing and leaves no cell empty."""
    total = len(energies)
    best = 1
    for n in divisors(total):
        if total // n < MIN_FRAME:
            continue
        if faults(energies, n) == (0, 0):
            best = max(best, n)
    return best


def inspect(path, entry):
    img = Image.open(path).convert('RGBA')
    if img.getchannel('A').getextrema()[0] == 255:
        return 'opaque', 'no alpha - grid cannot be measured', None

    col_flags, row_flags = energy(img)
    ccut, cempty = faults(col_flags, entry['cols'])
    rcut, rempty = faults(row_flags, entry['rows'])

    if (ccut, cempty, rcut, rempty) == (0, 0, 0, 0):
        return 'ok', '%dx%d holds up' % (entry['cols'], entry['rows']), None

    cols, rows = best_split(col_flags), best_split(row_flags)
    fw, fh = img.width // cols, img.height // rows

    problems = []
    if ccut or rcut:
        problems.append('%d cell edge(s) slice through a sprite' % (ccut + rcut))
    if cempty or rempty:
        problems.append('%d blank frame(s)' % (cempty + rempty))

    return ('broken',
            '%s; %dx%d -> %dx%d (%dx%d px)'
            % (', '.join(problems), entry['cols'], entry['rows'], cols, rows, fw, fh),
            {'cols': cols, 'rows': rows, 'frameWidth': fw, 'frameHeight': fh,
             'frames': cols * rows})


def trailing_blanks(img, entry):
    """How many cells at the end of the sheet hold nothing.

    Sheets are usually padded out to a round cell count, so the last frames are
    empty and the animation blinks off before looping. `frames` is what the
    loader plays, so shrinking it is enough - the PNG stays as it is.
    """
    fw, fh = entry['frameWidth'], entry['frameHeight']
    alpha = img.getchannel('A')
    blanks = 0
    for i in range(entry['frames'] - 1, 0, -1):
        x, y = (i % entry['cols']) * fw, (i // entry['cols']) * fh
        if alpha.crop((x, y, x + fw, y + fh)).getextrema()[1] >= ALPHA_FLOOR:
            break
        blanks += 1
    return blanks


def main(web_dir, apply_fix):
    manifest_path = os.path.join(web_dir, 'effects.json')
    with open(manifest_path, encoding='utf-8') as f:
        manifest = json.load(f)

    buckets = {'ok': [], 'broken': [], 'opaque': []}
    trimmed, overridden, promoted = [], [], []
    for e in manifest['assets']:
        path = os.path.join(web_dir, e['file'])
        if not os.path.exists(path):
            continue
        img = Image.open(path).convert('RGBA')

        promo = PROMOTIONS.get(e['id'])
        if promo and e['frames'] == 1:
            cols, rows, cat = promo
            promoted.append((e['id'], cols * rows, cat))
            if apply_fix:
                e.update({'cols': cols, 'rows': rows, 'frames': cols * rows,
                          'frameWidth': img.width // cols,
                          'frameHeight': img.height // rows,
                          'category': cat, 'fps': e.get('fps', 12)})
                new_rel = 'effects/' + os.path.basename(path)
                new_path = os.path.join(web_dir, new_rel)
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                os.replace(path, new_path)
                e['file'] = new_rel
                path = new_path

        override = GRID_OVERRIDES.get(e['id'])
        if override and (e['cols'], e['rows']) != override:
            cols, rows = override
            if apply_fix:
                e.update({'cols': cols, 'rows': rows, 'frames': cols * rows,
                          'frameWidth': img.width // cols,
                          'frameHeight': img.height // rows})
            overridden.append((e['id'], cols, rows))

        limit = FRAME_LIMITS.get(e['id'])
        if limit and e['frames'] != limit[0]:
            if apply_fix:
                e['frames'] = limit[0]
                e['note'] = limit[1]
            overridden.append((e['id'], limit[0], 1))

        blanks = trailing_blanks(img, e)
        if blanks:
            trimmed.append((e['id'], e['frames'], e['frames'] - blanks))
            if apply_fix:
                e['frames'] -= blanks

        verdict, detail, _ = inspect(path, e)
        buckets[verdict].append((e, detail))

    if apply_fix:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    print('grid ok %d | grid suspect %d | opaque(unmeasurable) %d | '
          'trailing blanks %d | overrides %d | promoted %d'
          % (len(buckets['ok']), len(buckets['broken']), len(buckets['opaque']),
             len(trimmed), len(overridden), len(promoted)))
    if promoted:
        print()
        print('== promoted to animations %s ==' % ('applied' if apply_fix else 'pending'))
        for aid, n, cat in promoted:
            print('  %-28s %d frames -> %s' % (aid, n, cat))
    if overridden:
        print()
        print('== grid overrides %s ==' % ('applied' if apply_fix else 'pending'))
        for aid, c, r in overridden:
            print('  %-28s -> %dx%d' % (aid, c, r))
    if trimmed:
        print('\n== trailing blank frames %s ==' % ('trimmed' if apply_fix else 'found'))
        for aid, was, now in trimmed:
            print('  %-28s %d -> %d frames' % (aid, was, now))
    for name in ('broken', 'opaque'):
        if not buckets[name]:
            continue
        print('\n== grid %s ==' % name)
        for e, detail in buckets[name]:
            print('  %-28s %s' % (e['id'], detail))


def default_library(root):
    """web/ while building, the package root once it has been shipped."""
    return root if os.path.exists(os.path.join(root, 'effects.json'))         else os.path.join(root, 'web')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main(args[0] if args else default_library(root), '--apply' in sys.argv)

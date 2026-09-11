# -*- coding: utf-8 -*-
"""Pack the usable effects into a few thumbnail atlases for the online catalog.

The local library under web/ is ~90 MB across 470 files - too many to upload
one by one. Every frame is scaled into a fixed cell and packed into 2048px
atlas pages, so the whole catalog ships as a handful of PNGs plus one small
JSON that the catalog page embeds inline.

    python tools/build_catalog.py

Writes catalog/atlas_N.png and catalog/catalog.json.
"""
import json
import math
import os

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# web/ while building, the package root once it has been shipped.
WEB = ROOT if os.path.exists(os.path.join(ROOT, 'effects.json')) else os.path.join(ROOT, 'web')
OUT = os.environ.get('CATALOG_OUT') or os.path.join(ROOT, 'catalog')

CELL = int(os.environ.get('CATALOG_CELL', 128))
ATLAS = int(os.environ.get('CATALOG_ATLAS', 2048))
COLS = ATLAS // CELL
PER_ATLAS = COLS * COLS
MAX_FRAMES = 48               # long loops get sampled down


def frame_indices(n):
    """Up to MAX_FRAMES evenly spaced indices covering the whole animation."""
    if n <= MAX_FRAMES:
        return list(range(n))
    return [round(i * (n - 1) / (MAX_FRAMES - 1)) for i in range(MAX_FRAMES)]


def direct_catalog():
    """Manifest for the shipped viewer: no atlases, real sheets side by side."""
    with open(os.path.join(WEB, 'effects.json'), encoding='utf-8') as f:
        manifest = json.load(f)
    usable = sorted((e for e in manifest['assets'] if not e.get('reference')),
                    key=lambda e: (e['category'], e['id']))
    entries = [{
        'id': e['id'], 'cat': e['category'], 'file': e['file'],
        'cols': e['cols'], 'rows': e['rows'],
        'start': 0, 'n': e['frames'],
        'fps': e.get('fps', 12), 'fw': e['frameWidth'], 'fh': e['frameHeight'],
        'frames': e['frames'], 'sheet': '%dx%d' % (e['width'], e['height']),
        'opaque': bool(e.get('opaque')),
    } for e in usable]
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'catalog.json'), 'w', encoding='utf-8') as f:
        json.dump({'cell': CELL, 'cols': COLS, 'perAtlas': PER_ATLAS,
                   'atlases': 0, 'assets': entries}, f,
                  ensure_ascii=False, separators=(',', ':'))
    print('direct catalog: %d assets, no atlases' % len(entries))


def main():
    if os.environ.get('CATALOG_DIRECT'):
        return direct_catalog()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(WEB, 'effects.json'), encoding='utf-8') as f:
        manifest = json.load(f)
    usable = [e for e in manifest['assets'] if not e.get('reference')]
    usable.sort(key=lambda e: (e['category'], e['id']))

    total_cells = sum(len(frame_indices(e['frames'])) for e in usable)
    n_atlas = math.ceil(total_cells / PER_ATLAS)
    side = COLS * CELL
    pages = [Image.new('RGBA', (side, side), (0, 0, 0, 0)) for _ in range(n_atlas)]

    entries, cell = [], 0
    for e in usable:
        path = os.path.join(WEB, e['file'])
        if not os.path.exists(path):
            continue
        try:
            sheet = Image.open(path).convert('RGBA')
        except Exception:
            continue

        idxs = frame_indices(e['frames'])
        fw, fh = e['frameWidth'], e['frameHeight']
        scale = min(CELL / fw, CELL / fh, 1.0)
        dw, dh = max(1, round(fw * scale)), max(1, round(fh * scale))
        ox, oy = (CELL - dw) // 2, (CELL - dh) // 2

        start = cell
        for i in idxs:
            page = pages[cell // PER_ATLAS]
            slot = cell % PER_ATLAS
            x, y = (slot % COLS) * CELL, (slot // COLS) * CELL
            src = sheet.crop(((i % e['cols']) * fw, (i // e['cols']) * fh,
                              (i % e['cols']) * fw + fw, (i // e['cols']) * fh + fh))
            if (dw, dh) != (fw, fh):
                src = src.resize((dw, dh), Image.LANCZOS)
            page.paste(src, (x + ox, y + oy))
            cell += 1

        entries.append({
            'id': e['id'],
            'cat': e['category'],
            'start': start,
            'n': len(idxs),
            'cols': e['cols'], 'rows': e['rows'],
            'fps': e.get('fps', 12),
            'fw': fw, 'fh': fh,
            'frames': e['frames'],
            'sheet': '%dx%d' % (e['width'], e['height']),
            'opaque': bool(e.get('opaque')),
            'file': e['file'],
        })

    for i, p in enumerate(pages):
        p.save(os.path.join(OUT, 'atlas_%d.png' % i), optimize=True)

    catalog = {
        'cell': CELL, 'cols': COLS, 'perAtlas': PER_ATLAS,
        'atlases': n_atlas, 'assets': entries,
    }
    with open(os.path.join(OUT, 'catalog.json'), 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, separators=(',', ':'))

    sizes = [os.path.getsize(os.path.join(OUT, 'atlas_%d.png' % i)) for i in range(n_atlas)]
    print('%d assets, %d cells, %d atlases' % (len(entries), cell, n_atlas))
    for i, s in enumerate(sizes):
        print('  atlas_%d.png %5.2f MB' % (i, s / 1e6))
    print('catalog.json %.1f KB | atlases total %.1f MB'
          % (os.path.getsize(os.path.join(OUT, 'catalog.json')) / 1e3, sum(sizes) / 1e6))


if __name__ == '__main__':
    main()

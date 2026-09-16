# -*- coding: utf-8 -*-
"""Convert raw Nine Corporation effect assets into a web-ready sprite library.

Output layout:
  web/effects/<id>.webp   animation spritesheets (horizontal strip or grid)
  web/textures/<id>.webp  single, non-animated images (incl. Unity particle textures)
  web/effects.json        manifest consumed by web/loader.js
"""
import hashlib
import json
import os
import re
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romanize import romanize

BACKSLASH = chr(92)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get('EFFECT_OUT') or os.path.join(ROOT, 'web')
MAX_SHEET_WIDTH = 4096
DEFAULT_FPS = 12

ALL_SOURCES = [
    ('06_effect', os.path.join(ROOT, '_raw_06')),
    ('effect_old', os.path.join(ROOT, '_raw_old')),
    ('012_effect', os.path.join(ROOT, '_raw_012')),
    ('unity', os.path.join(ROOT, '_unpacked')),
]
_only = os.environ.get('EFFECT_SOURCES')
SOURCES = ([s for s in ALL_SOURCES if s[0] in _only.split(',')] if _only else ALL_SOURCES)

CATEGORY_BY_DIR = {
    '01_투사체': 'projectile', '02_장판': 'zone', '03_피격': 'hit',
    '04_신화스킬': 'mythic', '01_버프_디버프': 'buff', '01_texture_effect': 'buff',
    '02_bg': 'background', '03_UI': 'ui', '04_기본공격': 'attack_basic',
    '05_연타': 'attack_combo', '06_일격': 'attack_heavy', '06_전체공격': 'attack_aoe',
    '07_특수공격': 'attack_special', '08_emotion': 'emotion', '09_무기이펙트': 'weapon',
    '10_펫': 'pet', '11_아우라_캐릭터': 'aura_character', '12_아우라_UI': 'aura_ui',
    '13_방치보상': 'idle_reward', '14_컨텐츠언락': 'content_unlock',
    '15_시즌패스': 'season_pass', '17_어드벤쳐보스': 'adventure_boss',
}

SIZE_RE = re.compile(r'_(\d{2,4})\s*[xX]\s*(\d{2,4})(?:\D|$)')
DATE_RE = re.compile(r'^\d{6}_')


def slugify(name):
    s = romanize(name).lower()
    s = re.sub(r'[^a-z0-9]+', '_', s)
    return re.sub(r'_+', '_', s).strip('_') or 'asset'


def asset_id(rel_path):
    stem = os.path.splitext(os.path.basename(rel_path))[0]
    stem = DATE_RE.sub('', stem)
    stem = SIZE_RE.sub('_', stem)
    return slugify(re.sub(r'_+$', '', stem))


def category_for(rel_path):
    for part in rel_path.replace(BACKSLASH, '/').split('/'):
        if part in CATEGORY_BY_DIR:
            return CATEGORY_BY_DIR[part]
    low = rel_path.lower()
    if 'world' in low or '월드' in rel_path:
        return 'world8'
    if 'aura' in low or '아우라' in rel_path:
        return 'aura_character'
    return 'misc'


def grid_from_filename(name, w, h):
    """Return (fw, fh, cols, rows) if the _WxH hint in the filename tiles evenly."""
    best = None
    for m in SIZE_RE.finditer(name):
        fw, fh = int(m.group(1)), int(m.group(2))
        if fw <= 0 or fh <= 0 or fw > w or fh > h:
            continue
        if w % fw or h % fh:
            continue
        cols, rows = w // fw, h // fh
        if cols * rows < 2:
            continue
        best = (fw, fh, cols, rows)
    return best


def grid_from_shape(w, h):
    """Fall back to a plain strip when one side is a whole multiple of the other."""
    if h and w % h == 0 and 2 <= w // h <= 32:
        return (h, h, w // h, 1)
    if w and h % w == 0 and 2 <= h // w <= 32:
        return (w, w, 1, h // w)
    return None


def frames_to_sheet(frames, fw, fh):
    """Lay frames out as a horizontal strip, wrapping into rows past MAX_SHEET_WIDTH."""
    n = len(frames)
    cols = max(1, min(n, MAX_SHEET_WIDTH // fw if fw else n))
    rows = (n + cols - 1) // cols
    sheet = Image.new('RGBA', (cols * fw, rows * fh), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        if fr.size != (fw, fh):
            canvas = Image.new('RGBA', (fw, fh), (0, 0, 0, 0))
            canvas.paste(fr, (0, 0))
            fr = canvas
        sheet.paste(fr, ((i % cols) * fw, (i // cols) * fh))
    return sheet, cols, rows


def read_gif(path):
    im = Image.open(path)
    frames, durations = [], []
    for i in range(im.n_frames):
        im.seek(i)
        frames.append(im.convert('RGBA').copy())
        d = im.info.get('duration', 0) or 0
        if d:
            durations.append(d)
    avg = sum(durations) / len(durations) if durations else 0
    fps = round(1000.0 / avg) if avg else DEFAULT_FPS
    return frames, max(1, min(60, fps))


def read_psd_layers(path):
    """PSD layers double as animation frames in this asset set; render each one."""
    from psd_tools import PSDImage
    psd = PSDImage.open(path)
    cw, ch = psd.size
    layers = [l for l in psd if l.kind == 'pixel' and l.bbox != (0, 0, 0, 0)]
    if len(layers) < 2:
        return None
    nums = [re.search(r'(\d+)\s*(?:\.\w+)?$', l.name or '') for l in layers]
    if all(nums):
        layers = [l for _, l in sorted(zip([int(m.group(1)) for m in nums], layers),
                                       key=lambda p: p[0])]
    frames = []
    for l in layers:
        try:
            img = l.topil()
        except Exception:
            continue
        if img is None:
            continue
        canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
        canvas.paste(img.convert('RGBA'), (l.left, l.top))
        frames.append(canvas)
    return frames if len(frames) >= 2 else None


def flatten_psd(path):
    from psd_tools import PSDImage
    img = PSDImage.open(path).composite(force=True)
    return img.convert('RGBA') if img is not None else None


def collect_files():
    files = []
    for src_name, root in SOURCES:
        if not os.path.isdir(root):
            continue
        for dirpath, _, names in os.walk(root):
            for n in names:
                if os.path.splitext(n)[1].lower() not in ('.png', '.gif', '.psd', '.jpg', '.jpeg'):
                    continue
                full = os.path.join(dirpath, n)
                rel = os.path.relpath(full, root).replace(BACKSLASH, '/')
                files.append((src_name, full, rel))
    # Prefer 06_effect over its OLD copy, and pre-rendered PNG/GIF over PSD sources.
    src_rank = {'06_effect': 0, '012_effect': 1, 'unity': 2, 'effect_old': 3}
    ext_rank = {'.png': 0, '.gif': 1, '.jpg': 2, '.jpeg': 2, '.psd': 3}
    files.sort(key=lambda f: (src_rank[f[0]], ext_rank[os.path.splitext(f[1])[1].lower()], f[2]))
    return files


def main():
    os.makedirs(os.path.join(OUT, 'effects'), exist_ok=True)
    os.makedirs(os.path.join(OUT, 'textures'), exist_ok=True)

    manifest, seen_hash, seen_id, skipped = [], {}, {}, []
    stats = {'sheet': 0, 'texture': 0, 'dup': 0, 'fail': 0, 'psd_frames': 0, 'gif': 0}

    for src_name, full, rel in collect_files():
        ext = os.path.splitext(full)[1].lower()
        try:
            with open(full, 'rb') as fh:
                digest = hashlib.md5(fh.read()).hexdigest()
        except Exception as e:
            skipped.append((rel, 'read: %s' % e)); stats['fail'] += 1; continue
        if digest in seen_hash:
            stats['dup'] += 1
            continue

        frames, still, fps, note = None, None, DEFAULT_FPS, None
        try:
            if ext == '.gif':
                frames, fps = read_gif(full)
                if len(frames) < 2:
                    frames, still = None, Image.open(full).convert('RGBA')
                else:
                    stats['gif'] += 1
            elif ext == '.psd':
                frames = read_psd_layers(full)
                if frames:
                    stats['psd_frames'] += 1
                else:
                    still = flatten_psd(full)
                    if still is None:
                        skipped.append((rel, 'psd composite empty')); stats['fail'] += 1; continue
            else:
                still = Image.open(full).convert('RGBA')
        except Exception as e:
            skipped.append((rel, '%s: %s' % (type(e).__name__, e))); stats['fail'] += 1; continue

        if frames:
            fw, fh = frames[0].size
            sheet, cols, rows = frames_to_sheet(frames, fw, fh)
            nframes = len(frames)
        else:
            w, h = still.size
            grid = grid_from_filename(os.path.basename(rel), w, h) or grid_from_shape(w, h)
            if grid:
                fw, fh, cols, rows = grid
                sheet, nframes = still, cols * rows
            else:
                fw, fh, cols, rows, nframes = w, h, 1, 1, 1
                sheet = still
                if SIZE_RE.search(os.path.basename(rel)):
                    note = 'filename size hint does not tile evenly; kept as single image'

        base_id = asset_id(rel)
        # Register every id we hand out, generated suffixes included - otherwise
        # "spark" + "spark" yields "spark_2", which then collides with a file
        # actually named spark_2.
        uid, n = base_id, 1
        while uid in seen_id:
            n += 1
            uid = '%s_%d' % (base_id, n)
        seen_id[uid] = True

        kind = 'effects' if nframes > 1 else 'textures'
        out_rel = '%s/%s.webp' % (kind, uid)
        # lossless+exact: identical pixels, including RGB under alpha=0
        sheet.save(os.path.join(OUT, out_rel), lossless=True, exact=True)
        seen_hash[digest] = uid
        stats['sheet' if nframes > 1 else 'texture'] += 1

        entry = {
            'id': uid,
            'category': category_for(rel),
            'file': out_rel,
            'width': sheet.width, 'height': sheet.height,
            'frameWidth': fw, 'frameHeight': fh,
            'frames': nframes, 'cols': cols, 'rows': rows,
            'source': '%s/%s' % (src_name, rel),
        }
        if nframes > 1:
            entry['fps'] = fps
        if note:
            entry['note'] = note
        manifest.append(entry)

    manifest.sort(key=lambda e: (e['category'], e['id']))
    with open(os.path.join(OUT, 'effects.json'), 'w', encoding='utf-8') as f:
        json.dump({'version': 1, 'defaultFps': DEFAULT_FPS, 'assets': manifest}, f,
                  ensure_ascii=False, indent=2)

    print(json.dumps(stats, indent=2))
    print('manifest entries:', len(manifest))
    if skipped:
        print('skipped %d:' % len(skipped))
        for r, e in skipped[:25]:
            print('  ', r, '|', e)


if __name__ == '__main__':
    main()

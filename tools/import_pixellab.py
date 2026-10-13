#!/usr/bin/env python3
"""Import PixelLab characters + UI panels that are not in the library yet.

Input: a folder holding what the PixelLab MCP download links return —
  <src>/chars/<character id>.zip   (GET https://api.pixellab.ai/mcp/characters/<id>/download)
  <src>/ui/<ui asset id>.png       (GET https://api.pixellab.ai/mcp/ui-assets/<id>/download)

Characters land in the `pixel` category of characters.json (next to the dh_*/mt_*
game sprites, most of which were made in PixelLab too), UI panels in a `ui`
category of icons.json. Everything is `px_*` and lossless WebP.

Never adds a duplicate: an entry is skipped when any of its frames (or their
mirror image) is pixel-identical, after trimming transparent margins, to a frame
already in the library. So listing a character here that the game sprites
already cover is harmless. Re-running replaces the previous px_* entries.

  python tools/import_pixellab.py <src>

Stamps its own `hash` fields. Don't run tools/stamp_hashes.js on a Windows checkout:
CRLF line endings change every Spine entry's hash there.
"""
import hashlib
import io
import json
import math
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
FPS = 10
MAX_COLS = 8

# PixelLab character id -> (library id, display name). Only ones the dh_*/mt_* sprites don't
# already cover: the other 25 characters in the PixelLab account (knight, invaders, necro,
# skeleton, imp_v2, Park fantasy hero, ...) are in the library as dh_*/mt_* already.
CHARACTERS = {
    '483e51c3-b66c-4f6e-afbe-959366c5fbd2': ('px_park_base_a', '박부장 회사원 (베이스 A)'),
    '050cb806-bd58-42e5-8e68-17a3ea32e1a1': ('px_park_base_b', '박부장 회사원 (베이스 B)'),
    'd37c671b-d4cf-4f68-9aa5-7880576f91b3': ('px_park_base_c', '박부장 회사원 (베이스 C)'),
    '8785b866-7389-4ed0-9147-e6d8ef261936': ('px_imp_winged', '임프 (박쥐 날개)'),
    '3c10252c-445f-4981-9f4d-05163f3841c4': ('px_demon_lord_chibi', '마왕 (꼬마 데몬 로드)'),
    'a2b40ad6-a9a7-445d-be9e-70c8201584f6': ('px_swordsman_8dir', '검사 (8방향)'),
    '82cb6c61-2fcc-4b8f-93ac-9a145381bf08': ('px_skeleton_8dir', '해골병 (8방향 소형)'),
}

# PixelLab UI asset id -> (library id, display name)
UI_ASSETS = {
    '1e9008c8-06b2-49ec-8ff0-9fed4a84a38b': ('px_ui_panel_a_blue', 'UI 패널 A (파란 창)'),
    '03b9922b-81bc-4853-8b9b-ef72077f7b48': ('px_ui_button_a_blue', 'UI 버튼 A (파랑)'),
    '7954566c-238d-4cbc-ace1-7b3c91517022': ('px_ui_panel_b_stone_gold', 'UI 패널 B (돌·금장)'),
    '348300bf-8463-4b17-a844-0db0988f13de': ('px_ui_button_b_stone_gold', 'UI 버튼 B (돌·금장) 세트'),
    'bc3379c8-b2eb-4dbe-9026-b87b5f50cb9d': ('px_ui_panel_c_iron_bone', 'UI 패널 C (철·뼈) 세트'),
    '3d92a272-ac97-4483-a85a-a5135c8a4a0c': ('px_ui_button_c_iron_bone', 'UI 버튼 C (철·뼈)'),
}

# PixelLab names custom animations after their prompt; give the common ones short clip names.
ANIM_RENAME = {
    'animating': 'idle',
    'falling_backward': 'death',
    'axis2_walk': 'walk',
    'axis2_death': 'death',
    'pitchfork_thrust_attack': 'attack',
}
ANIM_PREFIX_RENAME = (
    ('casting_', 'cast'),
    ('raising_', 'cast'),
    ('thrusting_', 'attack'),
    ('drawing_the_bow', 'attack'),
)
DIRECTION_ORDER = ['south', 'south-east', 'east', 'north-east', 'north', 'north-west', 'west', 'south-west']


def clip_name(raw):
    if raw in ANIM_RENAME:
        return ANIM_RENAME[raw]
    for prefix, name in ANIM_PREFIX_RENAME:
        if raw.startswith(prefix):
            return name
    return raw


def frame_keys(img):
    """Hashes of the trimmed frame and its mirror (game sprites are often stored flipped)."""
    img = img.convert('RGBA')
    box = img.getbbox()
    if not box:
        return set()
    img = img.crop(box)
    return {hashlib.sha1(str(v.size).encode() + v.tobytes()).hexdigest() for v in (img, ImageOps.mirror(img))}


def library_frame_keys():
    """Frame hashes of every non-px_ clip in the library."""
    keys = set()
    for manifest in ('characters.json', 'icons.json'):
        for a in json.loads((ROOT / manifest).read_text(encoding='utf-8'))['assets']:
            if a['id'].startswith('px_'):
                continue
            clips = a.get('animations') or ({'default': a} if a.get('file') else {})
            for c in clips.values():
                path = ROOT / c['file']
                if not path.exists():
                    continue
                with Image.open(path) as sheet:
                    sheet = sheet.convert('RGBA')
                for i in range(c['frames']):
                    x, y = (i % c['cols']) * c['frameWidth'], (i // c['cols']) * c['frameHeight']
                    keys |= frame_keys(sheet.crop((x, y, x + c['frameWidth'], y + c['frameHeight'])))
    return keys


def sheet_clip(frames, rel):
    """Lays frames out on a grid; returns (image, clip entry) — written only if the entry is kept."""
    fw = max(f.width for f in frames)
    fh = max(f.height for f in frames)
    cols = min(len(frames), MAX_COLS)
    rows = math.ceil(len(frames) / cols)
    sheet = Image.new('RGBA', (fw * cols, fh * rows), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, ((i % cols) * fw + (fw - f.width) // 2, (i // cols) * fh + (fh - f.height) // 2))
    clip = {
        'file': rel, 'width': sheet.width, 'height': sheet.height,
        'frameWidth': fw, 'frameHeight': fh, 'frames': len(frames), 'cols': cols, 'rows': rows,
    }
    if len(frames) > 1:
        clip['fps'] = FPS
    return sheet, clip


def save(pending):
    for sheet, clip in pending:
        out = ROOT / clip['file']
        out.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(out, lossless=True, exact=True)
        clip['hash'] = hashlib.sha1(out.read_bytes()).hexdigest()[:10]  # same as tools/stamp_hashes.js


def is_duplicate(frames, seen, lib_id):
    for f in frames:
        if frame_keys(f) & seen:
            print('skip, already in library:', lib_id)
            return True
    return False


def import_characters(src, seen):
    by_state = {}
    for z in sorted((src / 'chars').glob('*.zip')):
        archive = zipfile.ZipFile(z)
        meta = json.loads(archive.read('metadata.json'))
        for state in meta['states']:
            # A group zip carries every state of the group: register each state once.
            by_state.setdefault(state['character']['id'], (archive, state))

    entries = []
    for pl_id, (lib_id, name) in CHARACTERS.items():
        if pl_id not in by_state:
            print('missing download for', lib_id, pl_id)
            continue
        archive, state = by_state[pl_id]
        load = lambda path: Image.open(io.BytesIO(archive.read(path))).convert('RGBA')
        rotations = {d: load(p) for d, p in state['frames']['rotations'].items()}
        anims = {raw: {d: [load(p) for p in paths] for d, paths in by_dir.items()}
                 for raw, by_dir in state['frames'].get('animations', {}).items()}
        all_frames = list(rotations.values()) + [f for by_dir in anims.values() for fs in by_dir.values() for f in fs]
        if is_duplicate(all_frames, seen, lib_id):
            continue

        pending, animations = [], {}
        for raw, by_dir in anims.items():
            base = clip_name(raw)
            for direction, frames in by_dir.items():
                clip = base if len(by_dir) == 1 else f'{base}_{direction}'
                if clip in animations:
                    clip = raw if len(by_dir) == 1 else f'{raw}_{direction}'
                sheet, animations[clip] = sheet_clip(frames, f'characters/pixel/{lib_id}_{clip}.webp')
                pending.append((sheet, animations[clip]))
        for direction in sorted(rotations, key=DIRECTION_ORDER.index):
            sheet, animations[direction] = sheet_clip([rotations[direction]], f'characters/pixel/{lib_id}_{direction}.webp')
            pending.append((sheet, animations[direction]))
        save(pending)
        for f in all_frames:
            seen |= frame_keys(f)

        default = 'idle' if 'idle' in animations else next(iter(animations))
        animations = {default: animations.pop(default), **animations}
        char = state['character']
        entries.append({
            'id': lib_id,
            'name': name,
            'category': 'pixel',
            'defaultAnimation': default,
            'animations': animations,
            'note': f"PixelLab 캐릭터 ({char['size']['width']}x{char['size']['height']}, {char['directions']}방향). "
                    f"애니메이션은 east(오른쪽) 방향만 있고, 나머지 탭은 방향별 정지 그림. 원본 프롬프트: {char['prompt']}",
        })
    return entries


def import_ui(src, seen):
    entries = []
    for pl_id, (lib_id, name) in UI_ASSETS.items():
        path = src / 'ui' / f'{pl_id}.png'
        if not path.exists():
            print('missing download for', lib_id, pl_id)
            continue
        img = Image.open(path).convert('RGBA')
        img = img.crop(img.getbbox())  # PixelLab pads panels onto a fixed 384px canvas
        if is_duplicate([img], seen, lib_id):
            continue
        sheet, clip = sheet_clip([img], f'characters/ui/{lib_id}.webp')
        save([(sheet, clip)])
        seen |= frame_keys(img)
        entries.append({'id': lib_id, 'name': name, 'category': 'ui', **clip,
                        'note': 'PixelLab UI 패널 생성기로 만든 이미지 (투명 여백만 잘라냄)'})
    return entries


def save_manifest(rel, update):
    path = ROOT / rel
    raw = path.read_text(encoding='utf-8')
    manifest = json.loads(raw)
    update(manifest)
    eol = '\r\n' if '\r\n' in raw else '\n'
    text = json.dumps(manifest, ensure_ascii=False, indent=2).replace('\n', eol)
    path.write_text(text + (eol if raw.endswith('\n') else ''), encoding='utf-8', newline='')


def replace_px(manifest, entries):
    manifest['assets'] = [a for a in manifest['assets'] if not a['id'].startswith('px_')] + entries


def main():
    src = Path(sys.argv[1])
    for old in list((ROOT / 'characters' / 'pixel').glob('px_*')) + list((ROOT / 'characters' / 'ui').glob('px_*')):
        old.unlink()
    seen = library_frame_keys()
    chars = import_characters(src, seen)
    ui = import_ui(src, seen)

    existing = [a for f in ('characters.json', 'icons.json')
                for a in json.loads((ROOT / f).read_text(encoding='utf-8'))['assets'] if not a['id'].startswith('px_')]
    clash = {a['id'] for a in existing} & {e['id'] for e in chars + ui}
    clash |= {a['name'] for a in existing} & {e['name'] for e in chars + ui}
    if clash:
        sys.exit(f'id/name clash with existing entries: {sorted(clash)}')

    save_manifest('characters.json', lambda m: replace_px(m, chars))

    def add_ui(m):
        m['categories']['ui'] = 'UI'
        replace_px(m, ui)
    save_manifest('icons.json', add_ui)
    print(f'{len(chars)} characters, {len(ui)} UI panels')


if __name__ == '__main__':
    main()

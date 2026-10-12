#!/usr/bin/env python3
"""Imports the leftover candidates / drafts / older versions of the two games' characters.

Companion of import_game_sprites.py (same repos, same `pixel` category). Adds dh_* / mt_* entries whose
ids are not touched by that script (everything here has a suffix such as _v1, _draft, _cand, _src).
Not imported on purpose: backgrounds, towers, loading/store art, UI/product/trap icons and
the 박부장 costume parts (art/parts).

  python tools/import_game_candidates.py <day-hero-night-demon dir> <myeongtoe-hero dir>
  node tools/stamp_hashes.js
"""
import glob
import os
import re
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import import_game_sprites as base  # noqa: E402

ROOT = base.ROOT
DH_NAME = {k: v[0] for k, v in base.DH.items()}


def save(img, rel):
    dest = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    img.save(dest, lossless=True, exact=True)
    out = Image.open(dest)
    assert out.size == img.size and out.convert('RGBA').tobytes() == img.convert('RGBA').tobytes(), rel
    return img.size


def still(path, rel):
    im = Image.open(path)
    im.load()
    w, h = im.size
    return base.clip(rel, save(im, rel), w, h, 1, 1)


def strip(files, rel, fps):
    ims = [Image.open(f).convert('RGBA') for f in files]
    fw, fh = ims[0].size
    assert all(i.size == (fw, fh) for i in ims), files[0]
    sheet = Image.new('RGBA', (fw * len(ims), fh))
    for i, im in enumerate(ims):
        sheet.paste(im, (i * fw, 0))
    return base.clip(rel, save(sheet, rel), fw, fh, len(ims), fps)


def sheet_clip(path, rel, fw, fh, frames, fps):
    im = Image.open(path)
    im.load()
    return base.clip(rel, save(im, rel), fw, fh, frames, fps)


def frames_of(d):
    return sorted(glob.glob(os.path.join(d, '*.png')), key=lambda p: int(re.sub(r'\D', '', os.path.basename(p)) or 0))


def entry(cid, name, anims, note, default=None):
    e = base.entry(cid, name, 'pixel', anims, note)
    e['defaultAnimation'] = default or next(iter(anims))
    return e


def main(dh, mt):
    art = os.path.join(dh, 'art')
    new = []
    src = '낮엔 용사, 밤엔 마왕 (day-hero-night-demon)'

    # 1) 이전 버전 — art/frames/<unit>_<anim>_v1
    groups = {}
    for d in sorted(glob.glob(os.path.join(art, 'frames', '*_v1'))):
        m = re.match(r'(.+)_(idle|attack|death)_v1$', os.path.basename(d))
        groups.setdefault(m[1], {})[m[2]] = d
    for uid, anims in groups.items():
        clips = {a: strip(frames_of(d), f'characters/pixel/dh_{uid}_v1_{a}.webp', base.DH_FPS[a]) for a, d in anims.items()}
        new.append(entry(f'dh_{uid}_v1', f'{DH_NAME.get(uid, uid)} (이전 버전)', clips,
                         f'{src} — 지금 게임에 쓰는 것 이전의 애니메이션 프레임(art/frames/*_v1).'))

    # 2) new3 시안 — 늑대인간/버섯/눈의 프레임 초안과 대체 모션
    new3 = os.path.join(art, 'monsters/new3')
    draft = {
        'werewolf': ('늑대인간', 'ww', {'idle': 'idle', 'attack': 'attack', 'death': 'death', 'attack2': 'atk2', 'attack3': 'atk3'}),
        'mushroom': ('역병 버섯', 'mu', {'idle': 'idle', 'attack': 'attack', 'death': 'death', 'death2': 'death2', 'mud': None}),
        'eye': ('심연의 눈', 'ey', {'idle': 'idle', 'attack': 'attack', 'death': 'death'}),
    }
    for uid, (name, pre, anims) in draft.items():
        clips = {}
        for a, key in anims.items():
            stem = 'mud' if (uid == 'mushroom' and a == 'mud') else f'{pre}_{key}'
            files = frames_of_prefix(new3, stem)
            fps = 12 if 'attack' in a or a == 'mud' else (6 if a == 'idle' else 10)
            clips[a] = strip(files, f'characters/pixel/dh_{uid}_draft_{a}.webp', fps)
        new.append(entry(f'dh_{uid}_draft', f'{name} (시안)', clips,
                         f'{src} — art/monsters/new3 의 초안 프레임과 대체 모션(공격2·3, 사망2 등).', 'idle'))

    # 3) 샘플 — art/samples
    for uid in ('knight', 'skeleton'):
        clips = {a: strip(frames_of(os.path.join(art, 'samples', f'{uid}_{a}')), f'characters/pixel/dh_{uid}_sample_{a}.webp', base.DH_FPS[a])
                 for a in ('idle', 'attack', 'death')}
        new.append(entry(f'dh_{uid}_sample', f'{DH_NAME[uid]} (샘플)', clips, f'{src} — art/samples 초기 샘플 프레임.'))

    # 4) 안 쓴 해골 마왕 시트
    clips = {}
    for a, frames in (('idle', 4), ('attack', 7), ('death', 7)):
        clips[a] = sheet_clip(os.path.join(art, f'unused/lord_skull_{a}.png'), f'characters/pixel/dh_lord_skull_{a}.webp', 96, 96, frames, base.DH_FPS[a])
    new.append(entry('dh_lord_skull', '마왕 (해골)', clips, f'{src} — art/unused, 게임에 안 쓴 시트.'))

    # 5) 마왕 시즌 후보 4종 × 4안, 소환 후보
    for theme, name in (('frost', '서리 용'), ('gold', '황금 기사'), ('hydra', '히드라'), ('kraken', '크라켄')):
        clips = {f'c{i}': still(os.path.join(art, f'lord/season/{theme}_{i}.png'), f'characters/pixel/dh_lord_season_{theme}_cand_{i}.webp') for i in range(4)}
        new.append(entry(f'dh_lord_season_{theme}_cand', f'마왕 시즌 후보 · {name}', clips, f'{src} — art/lord/season, 같은 주제의 시안 4장(프레임 아님).'))
    clips = {f'c{i}': still(os.path.join(art, f'lord/summon/cand_{i}.png'), f'characters/pixel/dh_lord_summon_cand_{i}.webp') for i in range(4)}
    new.append(entry('dh_lord_summon_cand', '마왕 소환 후보', clips, f'{src} — art/lord/summon, 시안 4장(프레임 아님).'))

    # 6) 낱장 그림 — 시안/원본/베이스
    singles = []
    for p in sorted(glob.glob(os.path.join(art, 'monsters/concept/*_a.png'))):
        u = os.path.basename(p)[:-6]
        singles.append((f'dh_{u}_concept', f'{DH_NAME[u]} (콘셉트)', p, 'art/monsters/concept'))
    for p in sorted(glob.glob(os.path.join(art, 'monsters/*_char_east.png'))):
        u = os.path.basename(p)[:-14]
        singles.append((f'dh_{u}_orig', f'{DH_NAME[u]} (원본 이미지)', p, 'art/monsters, 시트를 만들기 전 정지 그림'))
    singles.append(('dh_golem_obj_orig', '돌 골렘 (오브젝트)', os.path.join(art, 'monsters/golem_obj.png'), 'art/monsters'))
    singles.append(('dh_werewolf_orig', '늑대인간 (원본 이미지)', os.path.join(new3, 'werewolf_east.png'), 'art/monsters/new3'))
    for p in sorted(glob.glob(os.path.join(art, 'invaders/*_east.png'))):
        u = os.path.basename(p)[:-9]
        singles.append((f'dh_{u}_orig', f'{DH_NAME[u]} (원본 이미지)', p, 'art/invaders'))
    for stem, name in (('imp_v2', '임프 v2'), ('imp_v3', '임프 v3'), ('lord_char_a', '마왕 (원본 A)'),
                       ('lord_pack_0', '마왕 팩 0'), ('lord_pack_1', '마왕 팩 1'), ('lord_pack_2', '마왕 팩 2'), ('lord_pack_3', '마왕 팩 3')):
        singles.append((f'dh_{stem}_orig', name, os.path.join(art, f'lord/{stem}.png'), 'art/lord'))
    for p in sorted(glob.glob(os.path.join(art, 'lord/summon/base_*.png'))):
        u = os.path.basename(p)[5:-4]
        singles.append((f'dh_{u}_base_summon', f'{DH_NAME.get(u, u)} (소환 베이스)', p, 'art/lord/summon'))
    for p in sorted(glob.glob(os.path.join(art, 'gear/*.png'))):
        u = os.path.basename(p)[:-4]
        label = u[5:] if u.startswith('base_') else u
        kind = '베이스' if u.startswith('base_') else '장비 외형'
        singles.append((f'dh_{u}_gear', f'{DH_NAME.get(label, label)} ({kind})', p, 'art/gear'))
    for cid, name, p, where in singles:
        new.append(entry(cid, name, {'default': still(p, f'characters/pixel/{cid}.webp')}, f'{src} — {where}.', 'default'))

    # 7) myeongtoe-hero: 박부장 머리 반짝임, 몬스터 원본(codex) 시트
    msrc = '명퇴용사 박부장 (myeongtoe-hero)'
    shine = Image.open(os.path.join(mt, 'art/park/fx/head_shine.png'))
    new.append(entry('mt_park_head_shine', '박부장 머리 반짝임',
                     {'default': sheet_clip(os.path.join(mt, 'art/park/fx/head_shine.png'), 'characters/pixel/mt_park_head_shine.webp', 11, 11, shine.size[0] // 11, 10)},
                     f'{msrc} — art/park/fx, 11×11 6프레임.', 'default'))
    for p in sorted(glob.glob(os.path.join(mt, 'art/monsters/src/*_codex.png'))):
        stem = os.path.basename(p)[:-10]
        mid = stem.replace('_old', '')
        nm = base_mt_name(mt, mid) + (' (이전 원본 시트)' if stem.endswith('_old') else ' (원본 시트)')
        cid = f'mt_{stem}_src'
        new.append(entry(cid, nm, {'default': still(p, f'characters/pixel/{cid}.webp')},
                         f'{msrc} — art/monsters/src, 몬스터를 만들기 전 생성 원본 시트(여러 포즈가 한 장에 있다).', 'default'))

    base.write_manifest(new, base.is_candidate)
    print(len(new), 'entries added')


def frames_of_prefix(d, stem):
    return sorted(glob.glob(os.path.join(d, stem + '_[0-9].png')), key=lambda p: int(re.search(r'_(\d+)\.png$', p)[1]))


_mt = {}


def base_mt_name(mt, mid):
    import json
    if not _mt:
        _mt.update(json.load(open(os.path.join(mt, 'art/monsters/monsters.json')))['monsters'])
    return _mt[mid]['name']


if __name__ == '__main__':
    main(*sys.argv[1:3])

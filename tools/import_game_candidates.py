#!/usr/bin/env python3
"""Imports the leftover candidates / drafts / older versions of the two games' characters.

Companion of import_game_sprites.py (same repos, same `pixel` category). Adds dh_* / mt_* entries whose
ids are not touched by that script (everything here has a suffix such as _draft, _cand, _orig).
Not imported on purpose: myeongtoe-hero head shine and art/monsters/src sheets, backgrounds, towers, loading/store art, UI/product/trap icons and
the 박부장 costume parts (art/parts).

  python tools/import_game_candidates.py <day-hero-night-demon dir> <myeongtoe-hero dir>
  node tools/stamp_hashes.js
"""
import glob
import hashlib
import json
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

    # (이전 버전 art/frames/*_v1 은 지금 캐릭터와 같은 모습이라 넣지 않는다.)

    # 2) new3 시안 — 늑대인간/버섯/눈의 프레임 초안과 대체 모션
    new3 = os.path.join(art, 'monsters/new3')
    draft = {
        'werewolf': ('늑대인간', 'ww', {'attack2': 'atk2', 'attack3': 'atk3'}),
        'mushroom': ('역병 버섯', 'mu', {'death2': 'death2', 'mud': None}),
    }
    for uid, (name, pre, anims) in draft.items():
        clips = {}
        for a, key in anims.items():
            stem = 'mud' if (uid == 'mushroom' and a == 'mud') else f'{pre}_{key}'
            files = frames_of_prefix(new3, stem)
            fps = 12 if 'attack' in a or a == 'mud' else (6 if a == 'idle' else 10)
            clips[a] = strip(files, f'characters/pixel/dh_{uid}_draft_{a}.webp', fps)
        new.append(entry(f'dh_{uid}_draft', f'{name} (시안)', clips,
                         f'{src} — art/monsters/new3 의 대체 모션(공격2·3, 사망2 등). 게임 시트와 같은 모션은 뺐다.'))

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

    # (myeongtoe-hero 의 박부장 머리 반짝임, 몬스터 원본 시트 art/monsters/src/*_codex 는 넣지 않는다.)

    new = drop_duplicates(new)
    base.write_manifest(new, base.is_candidate)
    print(len(new), 'entries added')


def clip_frames(c):
    im = Image.open(os.path.join(ROOT, c['file'])).convert('RGBA')
    fw, fh = c['frameWidth'], c['frameHeight']
    return tuple(hashlib.md5(im.crop(((i % c['cols']) * fw, (i // c['cols']) * fh, (i % c['cols']) * fw + fw,
                                       (i // c['cols']) * fh + fh)).tobytes()).hexdigest() for i in range(c['frames']))


def drop_duplicates(new):
    """Drops clips whose pixels already exist in an entry of import_game_sprites.py (whole clip, or a
    single still equal to any frame of one) and entries left without clips."""
    data = json.load(open(os.path.join(ROOT, 'characters.json'), encoding='utf-8'))
    seen_clips, seen_frames = set(), set()
    for a in data['assets']:
        if a['id'].startswith(('dh_', 'mt_')) and not base.is_candidate(a['id']):
            for c in a['animations'].values():
                fr = clip_frames(c)
                seen_clips.add(fr)
                seen_frames.update(fr)
    out = []
    for e in new:
        for k in list(e['animations']):
            c = e['animations'][k]
            fr = clip_frames(c)
            if fr in seen_clips or (len(fr) == 1 and fr[0] in seen_frames):
                os.remove(os.path.join(ROOT, c['file']))
                del e['animations'][k]
                print('duplicate, skipped:', e['id'], k)
        if e['animations']:
            if e['defaultAnimation'] not in e['animations']:
                e['defaultAnimation'] = next(iter(e['animations']))
            out.append(e)
    return out


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

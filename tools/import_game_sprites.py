#!/usr/bin/env python3
"""Imports the sprite sheets of two games into characters.json.

  Jujeongmin/day-hero-night-demon  public/sprites/<unit>_{idle,attack,death}.png (+ src/render/sprites.json)
  Jujeongmin/myeongtoe-hero        art/monsters/*_{idle,hurt,death}.png (+ monsters.json), art/park/*_strip.png

  python tools/import_game_sprites.py <day-hero-night-demon dir> <myeongtoe-hero dir>
  node tools/stamp_hashes.js

Re-running replaces the dh_* / mt_* entries and their webp files, nothing else.
"""
import glob
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# day-hero-night-demon: id -> (Korean name, shape guess). Everything lands in the `pixel` category;
# the shape guess is only kept for reference. Names come from the game's ko strings.
DH = {
    'knight': ('기사', 'humanoid'), 'archer': ('궁수', 'humanoid'), 'priest': ('성직자', 'humanoid'),
    'thief': ('도적', 'humanoid'), 'lancer': ('창병', 'humanoid'), 'mage': ('마법사', 'humanoid'),
    'paladin': ('성기사', 'humanoid'), 'captain': ('용사단장', 'humanoid'),
    'deathknight': ('데스 나이트', 'humanoid'), 'vampire': ('흡혈귀', 'humanoid'),
    'necro': ('네크로맨서', 'humanoid'), 'necro_lich': ('리치 왕', 'humanoid'),
    'necro_bone': ('뼈 갑옷 네크로맨서', 'humanoid'),
    'lord': ('마왕', 'humanoid'), 'lord_demon': ('마왕 (악마)', 'humanoid'),
    'lord_emperor': ('마왕 (황제)', 'humanoid'), 'lord_lich': ('마왕 (리치)', 'monster'),
    'lord_abyss': ('마왕 (심연)', 'monster'), 'lord_lava': ('마왕 (용암)', 'monster'),
    'lord_dragon': ('마왕 (용)', 'beast'), 'lord_hydra': ('마왕 (히드라)', 'beast'),
    'lord_spend1': ('마왕 외형 A', 'humanoid'), 'lord_summon1': ('마왕 외형 B', 'humanoid'),
    'werewolf': ('늑대인간', 'beast'), 'dragon': ('새끼 용', 'beast'),
    'dragon_knight': ('기사 용', 'beast'), 'dragon_royal': ('왕실 용', 'beast'),
    'spider': ('거미', 'beast'), 'spider_iron': ('강철 거미', 'beast'), 'spider_crown': ('거미 여왕', 'beast'),
    'slime': ('슬라임', 'monster'), 'slime_helm': ('기사 슬라임', 'monster'), 'slime_crown': ('슬라임 왕', 'monster'),
    'skeleton': ('해골병', 'monster'), 'skeleton_royal': ('해골 왕', 'monster'),
    'skeleton_dread': ('공포의 갑옷', 'monster'),
    'imp': ('임프', 'monster'), 'imp_king': ('임프 왕', 'monster'), 'imp_warlock': ('흑마법사 임프', 'monster'),
    'golem': ('돌 골렘', 'monster'), 'banshee': ('밴시', 'monster'),
    'mushroom': ('역병 버섯', 'monster'), 'eye': ('심연의 눈', 'monster'),
}
DH_FPS = {'idle': 6, 'attack': 12, 'death': 10}

# myeongtoe-hero monsters: shape guess, unused now that everything is `pixel`.
MT_CATEGORY = {
    'humanoid': ['baek_bujang', 'gangsi_sangmu', 'silijeok_timjang', 'golf_sangmu', 'sosong_timjang', 'judge_lich',
                 'deadline_timjang', 'legacy_sangmu', 'jeoseung_timjang', 'sujeonno_sangmu', 'nakhasan_jeonmu',
                 'chairman_demon_king', 'lee_ceo', 'card_audit_bujang', 'third_year_jooim', 'ppeongtwigi_gwajang',
                 'mz_sawon', 'love_daeri', 'airpod_mz', 'card_pixie', 'phone_imp', 'sales_goblin'],
    'beast': ['stapler_bat', 'clip_rat', 'necktie_snake', 'bug_beetle', 'cable_spider', 'piggy_boar', 'card_bat',
              'sticky_moth', 'redtape_worm', 'stamp_crab', 'calc_crab'],
}
PARK_FPS = {'idle': 4, 'walk': 9, 'attack': 13}
PARK_FRAMES = {'idle': 4, 'walk': 6, 'attack': 8}


# ids owned by import_game_candidates.py (leftover candidates / drafts / older versions)
CANDIDATE_RE = re.compile(r'(_v1|_draft|_sample|_orig|_cand|_gear|_concept|_base_summon)$|^dh_lord_skull$')


def is_candidate(cid):
    return bool(CANDIDATE_RE.search(cid))


def write_manifest(new, owns):
    """Replaces the dh_/mt_ entries `owns(id)` says are ours (and their files); leaves everything else."""
    path = os.path.join(ROOT, 'characters.json')
    data = json.loads(open(path, encoding='utf-8').read())
    mine = lambda a: a['id'].startswith(('dh_', 'mt_')) and owns(a['id'])
    fresh = {c['file'] for e in new for c in e['animations'].values()}
    for a in data['assets']:
        if mine(a):
            for c in a['animations'].values():
                if c['file'] not in fresh and os.path.exists(os.path.join(ROOT, c['file'])):
                    os.remove(os.path.join(ROOT, c['file']))
    ids = {e['id'] for e in new}
    data['categories']['pixel'] = '픽셀'
    data['assets'] = [a for a in data['assets'] if not mine(a) and a['id'] not in ids] + new
    open(path, 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def webp(src, dest):
    im = Image.open(src)
    im.load()
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    im.save(dest, lossless=True, exact=True)
    out = Image.open(dest)
    if im.size != out.size or im.convert('RGBA').tobytes() != out.convert('RGBA').tobytes():
        os.remove(dest)
        raise SystemExit('not pixel-identical: ' + src)
    return im.size


def clip(rel, size, fw, fh, frames, fps):
    w, h = size
    assert w % fw == 0 and h % fh == 0, (rel, size, fw, fh)
    cols = w // fw
    return {'file': rel, 'width': w, 'height': h, 'frameWidth': fw, 'frameHeight': fh,
            'frames': frames, 'cols': cols, 'rows': h // fh, 'fps': fps}


def entry(cid, name, cat, anims, note):
    return {'id': cid, 'name': name, 'category': 'pixel',
            'defaultAnimation': 'idle', 'animations': anims, 'note': note}


def main(dh_dir, mt_dir):
    new = []
    sprites = json.load(open(os.path.join(dh_dir, 'src/render/sprites.json')))
    for uid, (name, cat) in DH.items():
        anims = {}
        for a in ('idle', 'attack', 'death'):
            meta = sprites.get(f'{uid}_{a}')
            src = os.path.join(dh_dir, 'public/sprites', f'{uid}_{a}.png')
            if not meta or not os.path.exists(src):
                continue
            rel = f'characters/pixel/dh_{uid}_{a}.webp'
            size = webp(src, os.path.join(ROOT, rel))
            anims[a] = clip(rel, size, meta['w'], meta['h'], meta['frames'], DH_FPS[a])
        if anims:
            new.append(entry(f'dh_{uid}', name, cat, anims,
                             '낮엔 용사, 밤엔 마왕 (day-hero-night-demon) 스프라이트. 오른쪽/왼쪽 방향은 게임 코드에서 뒤집어 썼다.'))

    mons = json.load(open(os.path.join(mt_dir, 'art/monsters/monsters.json')))['monsters']
    cat_of = {m: c for c, ms in MT_CATEGORY.items() for m in ms}
    for mid, m in mons.items():
        cat = cat_of.get(mid, 'monster')
        anims = {}
        for a, spec in m['animations'].items():
            src = os.path.join(mt_dir, 'art/monsters', spec['file'])
            rel = f'characters/pixel/mt_{mid}_{a}.webp'
            size = webp(src, os.path.join(ROOT, rel))
            anims[a] = clip(rel, size, m['frameWidth'], m['frameHeight'], spec['frameCount'],
                            round(1000 / spec['frameDurationMs']))
        new.append(entry(f'mt_{mid}', m['name'], cat, anims,
                         f"명퇴용사 박부장 (myeongtoe-hero) {m['departmentName']} {m['role']}. 왼쪽(박부장 쪽)을 보고 있다."))

    anims = {}
    for a, n in PARK_FRAMES.items():
        src = os.path.join(mt_dir, f'art/park/{a}_strip.png')
        rel = f'characters/pixel/mt_park_{a}.webp'
        size = webp(src, os.path.join(ROOT, rel))
        anims[a] = clip(rel, size, 64, 64, n, PARK_FPS[a])
    new.append(entry('mt_park', '박부장', 'humanoid', anims,
                     '명퇴용사 박부장 (myeongtoe-hero) 주인공. 오른쪽을 보고 있다. 장비/의상 파츠(art/parts)는 안 넣었다.'))

    write_manifest(new, lambda cid: not is_candidate(cid))
    print(len(new), 'characters added')


if __name__ == '__main__':
    main(*sys.argv[1:3])

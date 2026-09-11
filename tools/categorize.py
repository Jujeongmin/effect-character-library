# -*- coding: utf-8 -*-
"""Re-file every effect by what it looks like, not which folder it came from.

build.py derives a category from the source folder, so everything under
`02_장판` landed in `zone` - explosions, lightning strikes, rings and sparks
included. These assignments were made by looking at the frames.

    python tools/categorize.py [library_dir]
"""
import json
import os
import sys
from collections import Counter

# category -> the effects that belong in it. Anything not listed keeps the
# category build.py gave it.
#
# The `mythic` set is deliberately gone: those nine shared nothing but the
# source game's purple rarity tint, so each one is filed by what it looks like.
CATEGORIES = {
    'explosion': [                       # 폭발 - 화구가 터지고 연기로 흩어짐
        'bomb_drop_1', 'bomb_drop_1_2', 'bomb_drop_1_3',
        'bomb_drop_2', 'bomb_drop_2_2', 'bomb_drop_2_3',
        'explosion', 'explosion_2', 'explosion_3', 'tyr_bomb',
        'mythic_bomb_drop_explode',
    ],
    'lightning': [                       # 번개 - 낙뢰, 전기 아크, 룬 서클
        'chain', 'lightning_2',
        'thor_lighting', 'thor_lightning', 'thor_thunder', 'thor_thunder2',
        'thunderstrike_wo_blur', 'thunderstrike_wo_blur_2',
        'spark', 'spark_150', 'spark_3', 'spark_4', 'spark_5', 'spark_7',
    ],
    'impact': [                          # 피격 - 맞은 순간 터지고 사라짐
        'deatheffect', 'deatheffect_2', 'manaball_hit', 'manaball_hit_2',
        'ricochet', 'ricochet_2', 'ricochet_3',
        'frost', 'frost_2', 'drain', 'drain_2', 'drain_3',
        'mythic_drain_on_hit', 'mythic_ricochet', 'mythic_volatile_shot',
    ],
    'zone': [                            # 장판 - 바닥에 깔려 지속되는 것만
        'poison', 'poison_2', 'poison_3', 'poison_4', 'poison_5',
        'poison_7', 'poison_9', 'posion', 'frost_zone',
        'mythic_frost_zone', 'mythic_poison_zone',
    ],
    'aura': [                            # 아우라 - 대상을 감싸는 고리와 불기둥
        'repulse', 'repulse_2', 'repulse_3',
        'ring', 'fire_ring_01', 'fire_aura', 'fire_auraball',
        'mythic_heal', 'mythic_repulse_aura',
    ],
    'projectile': ['mythic_bomb_drop_fall'],
}


def default_library(root):
    """web/ while building, the package root once it has been shipped."""
    return root if os.path.exists(os.path.join(root, 'effects.json')) \
        else os.path.join(root, 'web')


def categorize(lib_dir):
    path = os.path.join(lib_dir, 'effects.json')
    with open(path, encoding='utf-8') as f:
        manifest = json.load(f)

    wanted = {}
    for cat, ids in CATEGORIES.items():
        for i in ids:
            wanted[i] = cat

    known = {e['id'] for e in manifest['assets']}
    unknown = sorted(set(wanted) - known)

    changed = 0
    for e in manifest['assets']:
        cat = wanted.get(e['id'])
        if cat and e['category'] != cat:
            e['category'] = cat
            changed += 1

    manifest['assets'].sort(key=lambda e: (e['category'], e['id']))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print('recategorised %d of %d effects' % (changed, len(manifest['assets'])))
    for cat, n in Counter(e['category'] for e in manifest['assets']).most_common():
        print('  %-12s %d' % (cat, n))
    if unknown:
        print('listed but not in the library: %s' % ', '.join(unknown))


if __name__ == '__main__':
    args = sys.argv[1:]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    categorize(args[0] if args else default_library(root))

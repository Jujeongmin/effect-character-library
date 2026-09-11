# -*- coding: utf-8 -*-
"""Thin the particle list down to the designs that are actually distinct.

The original project made a prefab per weapon and per rarity colour, so the
344 recipes hold a lot of repetition:

  * identical designs   - same emitters, same numbers, same colours
  * colour variants     - same design, only the material tint differs
  * UI and reward art   - buff icons, menus, victory banners; not combat VFX

Identical designs collapse to one. Colour variants collapse to one entry that
carries the others in `variants`, each with its tint, so nothing is lost - the
runtime can recolour. UI families are dropped outright.

    python tools/dedupe_particles.py [library_dir] [--dry-run]
"""
import json
import os
import re
import sys
from collections import OrderedDict, defaultdict

UI_NAME = re.compile(r'(^|_)(ui|menu|buff|result|victory|levelup|stage)', re.I)
COLOUR = re.compile(r'_(blue|red|green|yellow|violet|purple|cyan|white|orange|pink|gold|silver)(?=_|$)',
                    re.I)


def signature(effect, with_tint):
    """What makes two recipes the same. Tint is optional so colour variants pair up."""
    rows = []
    for m in effect['emitters']:
        row = [m.get('texture'), m.get('maxParticles'), m.get('render'),
               json.dumps(m.get('lifetime'), sort_keys=True),
               json.dumps(m.get('speed'), sort_keys=True),
               json.dumps(m.get('size'), sort_keys=True),
               json.dumps(m.get('rate'), sort_keys=True),
               json.dumps(m.get('bursts'), sort_keys=True),
               json.dumps(m.get('shape'), sort_keys=True),
               json.dumps(m.get('sizeOverLife'), sort_keys=True)]
        if with_tint:
            row.append(json.dumps(m.get('tint'), sort_keys=True))
            row.append(json.dumps(m.get('color'), sort_keys=True))
        rows.append('|'.join(map(str, row)))
    return '||'.join(sorted(rows))


def family_key(name):
    """Name with its colour word and id numbers removed."""
    return re.sub(r'\d+', '#', COLOUR.sub('', name)).lower()


def pick(names):
    """Representative of a group: the shortest, then alphabetical."""
    return sorted(names, key=lambda n: (len(n), n))[0]


def tint_of(effect):
    for m in effect['emitters']:
        if m.get('tint'):
            return m['tint']
    for m in effect['emitters']:
        if m.get('color') and m['color'].get('color'):
            return m['color']['color']
    return None


def main(library, dry_run=False):
    path = os.path.join(library, 'particles.json')
    with open(path, encoding='utf-8') as f:
        spec = json.load(f)
    effects = spec['effects']
    start = len(effects)

    # 1. drop UI and reward art
    ui = [k for k in effects if UI_NAME.search(k)]
    for k in ui:
        del effects[k]

    # 2. identical designs, colours included
    exact = defaultdict(list)
    for k, v in effects.items():
        exact[signature(v, True)].append(k)
    dropped_exact = []
    for names in exact.values():
        if len(names) < 2:
            continue
        keep = pick(names)
        for n in names:
            if n != keep:
                dropped_exact.append(n)
                del effects[n]

    # 3. same design, different tint -> one entry carrying the variants
    fams = defaultdict(list)
    for k, v in effects.items():
        fams[signature(v, False)].append(k)
    folded = []
    for names in fams.values():
        if len(names) < 2:
            continue
        # Fold only when the names look like one family. Colours can sit
        # anywhere in the name, and the weapon auras are numbered per weapon,
        # so both are normalised away before comparing.
        stripped = {family_key(n) for n in names}
        if len(stripped) > 1:
            continue
        keep = pick(names)
        variants = []
        for n in sorted(names):
            variants.append({'id': n, 'tint': tint_of(effects[n])})
            if n != keep:
                folded.append(n)
                del effects[n]
        effects[keep]['variants'] = variants

    spec['effects'] = OrderedDict(sorted(effects.items()))
    if not dry_run:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(spec, f, ensure_ascii=False, separators=(',', ':'))

    print('%s%d -> %d particle effects' % ('[dry run] ' if dry_run else '', start, len(effects)))
    print('  UI / reward art dropped        %d' % len(ui))
    print('  identical designs dropped      %d' % len(dropped_exact))
    print('  colour variants folded in      %d' % len(folded))
    withvar = [k for k, v in effects.items() if v.get('variants')]
    print('  entries carrying variants      %d' % len(withvar))
    for k in withvar[:6]:
        print('    %-34s %s' % (k[:34], ', '.join(v['id'][-12:] for v in effects[k]['variants'])))
    if not dry_run:
        print('  file now %.0f KB' % (os.path.getsize(path) / 1024))


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    main(args[0] if args else root, '--dry-run' in sys.argv)

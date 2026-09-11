# -*- coding: utf-8 -*-
"""Inline catalog.json (and, once uploaded, the atlas asset ids) into the page.

    python tools/make_page.py                    # local build, reads atlas_N.png
    python tools/make_page.py id0 id1 id2 ...    # published build, reads /_blob/<id>
"""
import base64
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.environ.get('CATALOG_OUT') or os.path.join(ROOT, 'catalog')
# The template ships in tools/; a working tree may also keep one in catalog/.
TEMPLATE = next(p for p in (os.path.join(CAT, 'template.html'),
                            os.path.join(ROOT, 'tools', 'viewer-template.html'))
                if os.path.exists(p))


def embedded_atlases():
    """Read the atlas PNGs back as data URIs so the page is self-contained."""
    srcs = []
    for path in sorted(glob.glob(os.path.join(CAT, 'atlas_*.png')),
                       key=lambda p: int(os.path.basename(p)[6:-4])):
        with open(path, 'rb') as f:
            srcs.append('data:image/png;base64,' + base64.b64encode(f.read()).decode('ascii'))
    return srcs


def main(ids):
    with open(TEMPLATE, encoding='utf-8') as f:
        html = f.read()
    with open(os.path.join(CAT, 'catalog.json'), encoding='utf-8') as f:
        data = f.read()
    # The particle recipes ride along so the page works with no sibling files.
    pspec = os.path.join(ROOT, 'particles.json')
    particles = open(pspec, encoding='utf-8').read() if os.path.exists(pspec) else '{}'
    pjs = os.path.join(ROOT, 'particles.js')
    runtime = open(pjs, encoding='utf-8').read() if os.path.exists(pjs) else ''

    # The JSON sits in a <script type="application/json">; only "</" can break out.
    html = html.replace('/*__CATALOG__*/', data.replace('</', '<\\/'))
    html = html.replace('/*__PARTICLES__*/', particles.replace('</', '<\\/'))
    html = html.replace('/*__PARTICLES_JS__*/', runtime)
    html = html.replace('/*__ATLAS_SRC__*/[]', json.dumps(ids))

    out = os.environ.get('CATALOG_PAGE') or os.path.join(CAT, 'index.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print('wrote %s (%.2f MB), %d atlases %s'
          % (out, os.path.getsize(out) / 1e6, len(ids),
             'embedded' if ids else 'as sibling files'))


if __name__ == '__main__':
    args = sys.argv[1:]
    main(embedded_atlases() if args[:1] == ['--embed'] else args)

# -*- coding: utf-8 -*-
"""Pull the prefabs, materials and their GUID map out of the .unitypackage files.

The PNGs in singles/ are only the raw material a particle system emits. The
recipe - how many, how fast, how long they live, how they grow and fade - is in
the prefabs, and which texture each one draws is in the materials. Both are
plain YAML inside the package, so both can be read.

A .unitypackage is a gzipped tar of one folder per asset, named by its GUID and
holding `pathname` (where it lived in the project) and `asset` (the bytes).
That folder name is what lets a material's `{guid: ...}` reference be resolved
back to a texture.

    python tools/extract_unity_assets.py <zip> <out_dir>

Writes out_dir/prefabs/*.prefab, out_dir/materials/*.mat and out_dir/guids.json.
"""
import io
import json
import os
import sys
import tarfile
import zipfile

WANT = ('.prefab', '.mat')


def decoded_names(zf):
    for info in zf.infolist():
        if info.is_dir():
            continue
        name = info.filename
        if not (info.flag_bits & 0x800):
            try:
                name = name.encode('cp437').decode('cp949')
            except Exception:
                pass
        yield name, info


def package_entries(blob):
    """(guid, pathname, bytes|None) for every asset in one .unitypackage."""
    try:
        tf = tarfile.open(fileobj=io.BytesIO(blob), mode='r:gz')
    except Exception:
        return
    folders = {}
    for m in tf.getmembers():
        if not m.isfile():
            continue
        parts = m.name.split('/')
        if len(parts) < 2:
            continue
        folders.setdefault(parts[-2], {})[parts[-1]] = m
    for guid, files in folders.items():
        if 'pathname' not in files:
            continue
        try:
            pathname = tf.extractfile(files['pathname']).read().decode('utf-8').split('\n')[0].strip()
        except Exception:
            continue
        data = None
        if 'asset' in files:
            try:
                data = tf.extractfile(files['asset']).read()
            except Exception:
                data = None
        yield guid, pathname, data


def safe_name(guid, pathname):
    stem = os.path.splitext(os.path.basename(pathname))[0]
    keep = ''.join(c if (c.isalnum() or c in '._-') else '_' for c in stem)
    return '%s.%s' % (keep[:60] or 'asset', guid[:8])


def main(zip_path, out_dir):
    zf = zipfile.ZipFile(zip_path)
    pkgs = [i for n, i in decoded_names(zf) if n.lower().endswith('.unitypackage')]

    for sub in ('prefabs', 'materials'):
        os.makedirs(os.path.join(out_dir, sub), exist_ok=True)

    guids = {}
    written = {'prefab': 0, 'mat': 0}
    for n, info in enumerate(pkgs, 1):
        for guid, pathname, data in package_entries(zf.read(info)):
            # Every asset goes in the map, images included - materials point at
            # textures by GUID and we need the name on the other end.
            guids[guid] = pathname
            ext = os.path.splitext(pathname)[1].lower()
            if ext not in WANT or data is None:
                continue
            sub = 'prefabs' if ext == '.prefab' else 'materials'
            out = os.path.join(out_dir, sub, safe_name(guid, pathname) + ext)
            if not os.path.exists(out):
                with open(out, 'wb') as f:
                    f.write(data)
                written[ext.lstrip('.')] += 1
        if n % 40 == 0 or n == len(pkgs):
            print('  [%d/%d] %d prefabs, %d materials, %d guids'
                  % (n, len(pkgs), written['prefab'], written['mat'], len(guids)))

    with open(os.path.join(out_dir, 'guids.json'), 'w', encoding='utf-8') as f:
        json.dump(guids, f, ensure_ascii=False)
    print('done: %d prefabs, %d materials, %d guids mapped'
          % (written['prefab'], written['mat'], len(guids)))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

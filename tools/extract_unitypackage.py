"""Extract image assets out of .unitypackage files (gzipped tar, GUID-dir layout)."""
import tarfile, os, sys, io

IMG_EXT = {'.png', '.jpg', '.jpeg', '.tga', '.psd', '.gif', '.webp'}

def extract(pkg_path, out_root):
    written = []
    try:
        tf = tarfile.open(pkg_path, 'r:gz')
    except Exception as e:
        return written, f"OPEN FAIL {e}"
    members = {}
    for m in tf.getmembers():
        if not m.isfile():
            continue
        parts = m.name.split('/')
        if len(parts) < 2:
            continue
        guid, leaf = parts[-2], parts[-1]
        members.setdefault(guid, {})[leaf] = m
    for guid, files in members.items():
        if 'asset' not in files or 'pathname' not in files:
            continue
        try:
            pathname = tf.extractfile(files['pathname']).read().decode('utf-8').split('\n')[0].strip()
        except Exception:
            continue
        ext = os.path.splitext(pathname)[1].lower()
        if ext not in IMG_EXT:
            continue
        rel = pathname
        for prefix in ('Assets/', 'assets/'):
            if rel.startswith(prefix):
                rel = rel[len(prefix):]
        out = os.path.join(out_root, rel.replace(chr(92), '/'))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with tf.extractfile(files['asset']) as f, open(out, 'wb') as g:
            g.write(f.read())
        written.append(out)
    tf.close()
    return written, None

if __name__ == '__main__':
    src_root, out_root = sys.argv[1], sys.argv[2]
    pkgs = []
    for dirpath, _, names in os.walk(src_root):
        for n in names:
            if n.lower().endswith('.unitypackage'):
                pkgs.append(os.path.join(dirpath, n))
    print(f"{len(pkgs)} unitypackages found")
    total, fails = 0, []
    for i, p in enumerate(sorted(pkgs), 1):
        stem = os.path.splitext(os.path.basename(p))[0]
        w, err = extract(p, os.path.join(out_root, stem))
        if err:
            fails.append((p, err))
        total += len(w)
        if i % 20 == 0 or i == len(pkgs):
            print(f"  [{i}/{len(pkgs)}] {total} images so far")
    print(f"DONE {total} images extracted, {len(fails)} failures")
    for p, e in fails[:20]:
        print("  FAIL", os.path.basename(p), e)

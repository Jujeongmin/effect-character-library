#!/usr/bin/env python3
"""PNG -> lossless WebP, pixel-identical.

`exact=True` keeps the RGB values under fully-transparent pixels, which
plain lossless mode is free to rewrite - spine atlas pages care.

  python tools/to_webp.py <src.png> [dest.webp]   convert one file
  python tools/to_webp.py --all                   convert every tracked PNG
"""
import os
import subprocess
import sys

from PIL import Image


def convert(src, dest=None, remove_src=False):
    dest = dest or os.path.splitext(src)[0] + ".webp"
    im = Image.open(src)
    im.load()
    im.save(dest, lossless=True, exact=True)
    out = Image.open(dest)
    if im.size != out.size or im.convert("RGBA").tobytes() != out.convert("RGBA").tobytes():
        os.remove(dest)
        raise SystemExit("not pixel-identical: " + src)
    if remove_src:
        os.remove(src)
    return dest


def tracked_pngs():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw = subprocess.check_output(
        ["git", "-c", "core.quotepath=false", "ls-files", "-z", "--", "*.png", "*.PNG"], cwd=root)
    return root, [p for p in raw.decode("utf-8").split("\x00") if p]


def main():
    if sys.argv[1:2] == ["--all"]:
        root, pngs = tracked_pngs()
        os.chdir(root)
        for i, rel in enumerate(pngs, 1):
            convert(rel, remove_src=True)
            if i % 200 == 0:
                print("converted", i, "/", len(pngs))
        print("converted", len(pngs), "files")
    elif len(sys.argv) >= 2:
        print(convert(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()

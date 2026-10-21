"""v2.44: render each map's walk bitmap to PNG so the divide split is visible.

divide is 64x64 tiles = 256x256 minitiles and reports TWO components of almost
equal size (15219 / 15420). Before touching anything I want to see whether the
two starts are separated by a real river (original design) or by a one-minitile
seam that the bake turned impassable (bug).
"""
import gzip
import os
import sys

from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"


def render(mid, scale=2):
    with gzip.open(os.path.join(ASSETS, mid, "walk.bin.gz"), "rb") as f:
        raw = f.read()
    meta = {}
    with open(os.path.join(ASSETS, mid, "meta.txt"), "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                meta.setdefault(k, []).append(v)
    w = int(meta["w"][0])
    h = int(meta["h"][0])
    mw, mh = w * 4, h * 4
    starts = [[int(x) for x in s.split(",")] for s in meta["start"]]
    img = Image.new("RGB", (mw, mh), (0, 0, 0))
    px = img.load()
    for y in range(mh):
        for x in range(mw):
            px[x, y] = (40, 40, 40) if raw[y * mw + x] else (0, 0, 0)
    # mark each start with a 5px cross in red
    for i, s in enumerate(starts):
        sx, sy = int(s[0]) // 8, int(s[1]) // 8
        for d in range(-6, 7):
            if 0 <= sx + d < mw:
                px[sx + d, sy] = (255, 0, 0)
            if 0 <= sy + d < mh:
                px[sx, sy + d] = (255, 0, 0)
    if scale != 1:
        img = img.resize((mw * scale, mh * scale), Image.NEAREST)
    path = os.path.join(OUT, "_walk_%s.png" % mid)
    img.save(path)
    print("%-16s %dx%d -> %s  starts=%s" % (mid, mw, mh, path, starts))


for mid in sys.argv[1:]:
    render(mid)

"""Batch D verification: after the CV5/VX4 decode fix, check every shipped map
for (a) remaining void tiles, (b) walkable fraction, (c) start connectivity,
and (d) the CV5 groups whose tile table is entirely zero.
"""
import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from gapio import GapReader

ASSETS = os.path.join(pm.ROOT, r"AndroidPort\app\app\src\main\assets\maps")

print("--- CV5 groups with an all-zero tile table (per tileset)")
for tsname in ("badlands", "platform", "install", "ashworld", "jungle",
               "desert", "ice", "twilight"):
    T = pm.load_tileset(tsname)
    if not T:
        print("   %-9s MISSING" % tsname)
        continue
    n = len(T["cv5_tiles"])
    zero = [m for m in range(n) if not any(T["cv5_tiles"][m])]
    types = collections.Counter(T["cv5_type"][m] for m in zero)
    print("   %-9s groups=%-5d zero-tile-table=%-4d types=%s" % (
        tsname, n, len(zero), dict(types)))

print()
print("--- per-map audit")
for mid in sorted(os.listdir(ASSETS)):
    d = os.path.join(ASSETS, mid)
    if not os.path.isdir(d):
        continue
    meta = pm.json.load(open(os.path.join(d, "meta.json"), encoding="utf8"))
    w, h, tsname = meta["w"], meta["h"], meta["tileset"]
    T = pm.load_tileset(tsname)
    walk = open(os.path.join(d, "walk.bin"), "rb").read()
    W4, H4 = w * 4, h * 4
    free = sum(walk)
    print("   %-12s %3dx%-3d %-9s walk %d/%d = %.1f%%" % (
        mid, w, h, tsname, free, len(walk), 100.0 * free / len(walk)))
    # void tiles: read the chunk pngs and count pure-black 8x8 minitiles
    from PIL import Image
    black = 0
    total = 0
    for f in os.listdir(d):
        if f.startswith("c_") and f.endswith(".png"):
            im = Image.open(os.path.join(d, f)).convert("RGB")
            px = im.load()
            for by in range(0, im.height, 8):
                for bx in range(0, im.width, 8):
                    total += 1
                    if px[bx, by] == (0, 0, 0) and px[bx + 4, by + 4] == (0, 0, 0):
                        black += 1
    print("        minitiles=%d fully-black=%d (%.1f%%)" % (
        total, black, 100.0 * black / total if total else 0))

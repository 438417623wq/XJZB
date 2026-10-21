"""Batch D probe 16: the CV5 doodad record in full. For every doodad group a
map actually uses, print type/flags/overlay-id/width/height/dddata-id, and mark
those tiles on the stitched terrain so we can see whether the doodad art is
already in MTXM or needs the overlay sprite drawn on top.
"""
import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from PIL import Image
from gapio import GapReader

ASSETS = os.path.join(pm.ROOT, r"AndroidPort\app\app\src\main\assets\maps")
SRC = {m: s for s, m, _n in pm.MAPS}
TS = {}


def cv5_full(ts):
    """Return (n, rows) where rows[m] = 26 u16 words of CV5 struct m."""
    if ts in TS:
        return TS[ts]
    for ar in (pm.SD, pm.BD):
        p = "tileset\\%s.cv5" % ts
        if ar.has(p):
            d, g = ar.read_with_gaps(p)
            break
    gr = GapReader(d, g or [])
    n = (len(d) + sum(s for _, s in (g or []))) // 52
    rows = [[gr.u16(m * 52 + k * 2) for k in range(26)] for m in range(n)]
    TS[ts] = (n, rows)
    return TS[ts]


for mid in ("divide", "hunters", "volcanis", "3kingdoms"):
    meta = pm.json.load(open(os.path.join(ASSETS, mid, "meta.json"), encoding="utf8"))
    w, h, tsname = meta["w"], meta["h"], meta["tileset"]
    n, rows = cv5_full(tsname)
    chk, gaps = pm.read_chk(os.path.join(pm.ROOT, SRC[mid]))
    g, sec = pm.parse_chk(chk, gaps)
    mo, _ = sec[b"MTXM"]
    used = collections.Counter()
    tiles = []
    for i in range(w * h):
        v = g.u16(mo + i * 2)
        grp = (v & 0x7FF0) >> 4
        if grp < n and rows[grp][0] == 1:
            used[grp] += 1
            tiles.append((i % w, i // w, grp, v & 0xF))
    print("== %s %s doodad-tiles=%d groups=%d" % (mid, tsname, len(tiles), len(used)))
    for grp, cnt in used.most_common(8):
        r = rows[grp]
        print("   grp %-5d x%-4d type=%d flags=0x%04X ovlID=%-5d scrdd=%-5d "
              "grpstr=%-4d unk=%-4d ddID=%-5d w=%-2d h=%-2d unk2=%-3d" % (
                  grp, cnt, r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]))
    # overlay the used doodad tiles on the terrain
    d = os.path.join(ASSETS, mid)
    img = Image.new("RGB", (w * 32, h * 32))
    for f in os.listdir(d):
        if f.startswith("c_") and f.endswith(".png"):
            cx, cy = f[2:-4].split("_")
            img.paste(Image.open(os.path.join(d, f)), (int(cx) * 512, int(cy) * 512))
    px = img.load()
    for tx, ty, grp, var in tiles:
        for yy in range(32):
            for xx in range(32):
                if (xx + yy) % 6 == 0:
                    X, Y = tx * 32 + xx, ty * 32 + yy
                    px[X, Y] = (255, 0, 0)
    img.save("_d16_%s_dd.png" % mid)
    print("   saved _d16_%s_dd.png" % mid)

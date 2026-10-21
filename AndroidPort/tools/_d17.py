"""Batch D probe 17: are doodad tiles walkable?

Doodads are baked into MTXM (so the plan's separate doodad layer is
unnecessary), which leaves one functional question: do the big ones -- trees,
rocks -- block movement, as batch D requires? Group doodad tiles by their CV5
record and report the walkable fraction per (ddID, w, h).
"""
import os, sys, gzip, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from gapio import GapReader

ASSETS = os.path.join(pm.ROOT, r"AndroidPort\app\app\src\main\assets\maps")
SRC = {m: s for s, m, _n in pm.MAPS}
_CV = {}


def cv5_full(ts):
    if ts in _CV:
        return _CV[ts]
    for ar in (pm.SD, pm.BD):
        p = "tileset\\%s.cv5" % ts
        if ar.has(p):
            d, g = ar.read_with_gaps(p)
            break
    gr = GapReader(d, g or [])
    n = (len(d) + sum(s for _, s in (g or []))) // 52
    rows = [[gr.u16(m * 52 + k * 2) for k in range(26)] for m in range(n)]
    _CV[ts] = (n, rows)
    return _CV[ts]


for mid in ("divide", "hunters", "3kingdoms", "volcanis", "darkcrystal", "bloodbath"):
    meta = pm.json.load(open(os.path.join(ASSETS, mid, "meta.json"), encoding="utf8"))
    w, h, tsname = meta["w"], meta["h"], meta["tileset"]
    n, rows = cv5_full(tsname)
    ts = pm.load_tileset(tsname)
    fl = ts["vf4_flags"]
    with gzip.open(os.path.join(ASSETS, mid, "walk.bin.gz"), "rb") as f:
        walk = f.read()
    chk, gaps = pm.read_chk(os.path.join(pm.ROOT, SRC[mid]))
    g, sec = pm.parse_chk(chk, gaps)
    mo, _ = sec[b"MTXM"]
    agg = collections.defaultdict(lambda: [0, 0, 0])   # tiles, fully-blocked, fully-open
    for i in range(w * h):
        raw = g.u16(mo + i * 2)
        grp, var = (raw & 0x7FF0) >> 4, raw & 0xF
        if grp >= n or rows[grp][0] != 1:
            continue
        vx4m = rows[grp][10 + var]          # CV5 @20 bytes = word 10
        if vx4m >= len(fl) or fl[vx4m] is None:
            continue
        s = sum(1 for k in range(16) if fl[vx4m][k] & 0x0001)
        r = rows[grp]
        a = agg[(r[6], r[7], r[8])]         # ddID, w, h
        a[0] += 1
        a[1] += 1 if s == 0 else 0
        a[2] += 1 if s == 16 else 0
    print("== %s %s doodad-groups=%d" % (mid, tsname, len(agg)))
    for key in sorted(agg, key=lambda k: -agg[k][0])[:8]:
        ddID, dw, dh = key
        t, blk, opn = agg[key]
        print("   ddID=%-5d w=%-2d h=%-2d tiles=%-4d fully-blocked=%-4d fully-open=%-4d"
              % (ddID, dw, dh, t, blk, opn))

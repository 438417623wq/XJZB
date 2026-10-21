"""Objective tileset-mapping test.

MTXM tile indices are tileset-specific: a map authored for tileset T has all of
its indices valid inside T's CV5 table. Rendering with the wrong tileset yields
out-of-range indices. So, for each map, the correct tileset is the one with
zero (or near-zero) out-of-range lookups -- an objective answer, no eyeballing.
"""
import os
import pipeline_maps as pm

CANDS = ["badlands", "platform", "install", "ashworld", "jungle",
         "desert", "ice", "twilight"]


def stats(map_src, ts_name):
    r = pm.read_chk(os.path.join(pm.ROOT, map_src))
    if not r:
        return None
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    if b"DIM " not in sec or b"MTXM" not in sec:
        return None
    off, _ = sec[b"DIM "]
    w, h = g.u16(off), g.u16(off + 2)
    off, _ = sec[b"MTXM"]
    mtwm = [g.u16(off + i * 2) for i in range(w * h)]
    ts = pm.load_tileset(ts_name)
    if ts is None:
        return None
    n_mega = len(ts["mega_vx4"])
    n_vx4 = len(ts["vx4_refs"])
    bad1 = 0          # index beyond the CV5 table
    bad2 = 0          # CV5 -> VX4 reference beyond the VX4 table
    for v in mtwm:
        if v >= n_mega:
            bad1 += 1
            continue
        if ts["mega_vx4"][v] >= n_vx4:
            bad2 += 1
    return w, h, len(mtwm), bad1, bad2, n_mega, n_vx4


print("map          ERA  pipeline->   " +
      "  ".join("%-9s" % c for c in CANDS))
print("-" * 118)
for src, mid, name in pm.MAPS:
    try:
        r = pm.read_chk(os.path.join(pm.ROOT, src))
        if not r:
            continue
        chk, gaps = r
        g, sec = pm.parse_chk(chk, gaps)
        era = g.byte(sec[b"ERA "][0]) if b"ERA " in sec else -1
        cur = pm.TILESETS.get(era, "?")
        cells = []
        for c in CANDS:
            s = stats(src, c)
            if s is None:
                cells.append("%-9s" % "-")
            else:
                w, h, n, b1, b2, nm, nv = s
                tag = "OK" if (b1 + b2) == 0 else "%d/%d" % (b1, b2)
                cells.append("%-9s" % tag)
        print("%-12s %-4d %-12s " % (mid, era, cur) + "  ".join(cells))
    except Exception as e:
        print("%-12s err %s" % (mid, e))

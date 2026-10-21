"""Batch D probe 3: are the all-zero CV5 tile arrays a gap artifact?

Prints the gap list of each tileset cv5 and the raw (pre-gap) bytes of the
groups whose u16[16] tile table reads as zero.
"""
import os, sys
sys.path.insert(0, ".")
import pipeline_maps as pm
from gapio import GapReader

TILESET = {0: "badlands", 1: "platform", 2: "install", 3: "ashworld",
           4: "jungle", 5: "desert", 6: "ice", 7: "twilight"}


def rd(ts, ext):
    for ar in (pm.SD, pm.BD):
        p = "tileset\\%s.%s" % (ts, ext)
        if ar.has(p):
            d, g = ar.read_with_gaps(p)
            return d, (g or []), (len(d) + sum(s for _, s in (g or [])))
    return None, [], 0


for ts in ("platform", "jungle"):
    d, gaps, full = rd(ts, "cv5")
    print("== %s short=%d gaps=%d full=%d groups_full=%d" % (
        ts, len(d), len(gaps), full, full // 52))
    print("   gaps:", gaps)
    for grp in (0, 1, 2, 3, 4, 5, 1254, 1441):
        b = grp * 52
        if b + 52 > full:
            continue
        # map original byte offsets to short offsets
        def sh(o):
            """original offset -> (short offset, in_gap)"""
            acc = 0
            for gp, gs in gaps:
                if o < gp:
                    return acc + (o - (gp - acc)), False
                if o < gp + gs:
                    return acc + (gp - acc), True
                acc -= gs
            return o, False
        o, ing = sh(b + 20)
        raw = d[o:o + 32] if not ing else b""
        vals = [raw[i] | (raw[i + 1] << 8) for i in range(0, len(raw), 2)]
        cv = GapReader(d, gaps)
        print("   grp %4d in_gap=%s raw=%s -> gapreader=%s" % (
            grp, ing, vals,
            [cv.u16(b + 20 + k * 2) for k in range(16)]))

"""Batch D probe 2: why do some correctly-decoded tiles render black?

Dumps the CV5 groups reached by bloodbath MTXM, grouped by terrain type, with
their flags / overlay / ddDataIndex / width / height / first megatile refs.
Also reports whether load_tileset's gap-shortened cv5 count differs from the
true 52-byte-record count (which would clamp valid groups to 0).
"""
import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from gapio import GapReader

TILESET = {0: "badlands", 1: "platform", 2: "install", 3: "ashworld",
           4: "jungle", 5: "desert", 6: "ice", 7: "twilight"}


def load_cv5(ts):
    for ar in (pm.SD, pm.BD):
        p = "tileset\\%s.cv5" % ts
        if ar.has(p):
            d, g = ar.read_with_gaps(p)
            return GapReader(d, g or []), (len(d) + sum(s for _, s in (g or []))), len(d)
    return None, 0, 0


def main():
    for mid, src in (("bloodbath", r"maps\(4)Blood Bath.scm"),
                     ("divide", r"maps\(2)The Small Divide.scm")):
        chk, gaps = pm.read_chk(os.path.join(pm.ROOT, src))
        g, sec = pm.parse_chk(chk, gaps)
        o, _ = sec[b"DIM "]
        w, h = g.u16(o), g.u16(o + 2)
        eo, _ = sec[b"ERA "]
        ts = TILESET.get(g.byte(eo), "platform")
        cv, full, short = load_cv5(ts)
        n = full // 52
        print("== %s  ts=%s  cv5 full=%d short=%d  n=%d  pm_n=%d" % (
            mid, ts, full, short, n, len(pm.load_tileset(ts)["mega_vx4"])))
        mo, _ = sec[b"MTXM"]
        vals = [g.u16(mo + i * 2) for i in range(w * h)]
        by_type = collections.defaultdict(set)
        for v in vals:
            grp = (v & 0x7FF0) >> 4
            by_type[cv.u16(grp * 52)].add(grp)
        for t in sorted(by_type):
            grps = sorted(by_type[t])
            print("  type %-3d groups %d  e.g. %s" % (t, len(grps), grps[:6]))
            for grp in grps[:3]:
                b = grp * 52
                tiles = [cv.u16(b + 20 + k * 2) for k in range(16)]
                print("      grp %4d flags=0x%04X ovl=%-4d dd=%-4d w=%d h=%d tiles=%s" % (
                    grp, cv.u16(b + 2), cv.u16(b + 4), cv.u16(b + 12),
                    cv.u16(b + 14), cv.u16(b + 16), tiles[:8]))
        # how many map tiles clamp under the gap-shortened count?
        pmn = len(pm.load_tileset(ts)["mega_vx4"])
        clamp = sum(1 for v in vals if ((v & 0x7FF0) >> 4) >= pmn)
        print("  tiles clamped by pm_n=%d: %d" % (pmn, clamp))


main()

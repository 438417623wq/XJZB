"""Batch D probe 1: correct MTXM decode + CV5 group census + doodad overlay resolution.

MTXM u16 = (group << 4) | tileIndex  (group = (v & 0x7FF0) >> 4).
CV5 group 52B: @0 type(1=doodad) @2 flags @4 overlayID @6 scr @8 grpstr @10 unk
               @12 ddDataIndex @14 w @16 h @18 unk @20 u16[16] vx4 megatile refs
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
            return GapReader(d, g or []), (len(d) + sum(s for _, s in (g or []))) // 52
    return None, 0


def main():
    for mid, src in (("bloodbath", r"maps\(4)Blood Bath.scm"),
                     ("divide", r"maps\(2)The Small Divide.scm"),
                     ("river", r"maps\(2)River Crossing.scm"),
                     ("hunters", r"maps\(8)The Hunters.scm")):
        chk, gaps = pm.read_chk(os.path.join(pm.ROOT, src))
        g, sec = pm.parse_chk(chk, gaps)
        o, _ = sec[b"DIM "]
        w, h = g.u16(o), g.u16(o + 2)
        eo, _ = sec[b"ERA "]
        ts = TILESET.get(g.byte(eo), "platform")
        cv, n = load_cv5(ts)
        types = collections.Counter()
        for m in range(n):
            types[cv.u16(m * 52)] += 1
        mo, _ = sec[b"MTXM"]
        raw = [g.u16(mo + i * 2) for i in range(w * h)]
        bad_raw = sum(1 for v in raw if v >= n)
        bad_new = sum(1 for v in raw if ((v & 0x7FF0) >> 4) >= n)
        # terrain type census of the correctly decoded map
        tcount = collections.Counter()
        for v in raw:
            grp = (v & 0x7FF0) >> 4
            tcount[cv.u16(grp * 52)] += 1
        # DD2
        dd = []
        if b"DD2 " in sec:
            do, ds = sec[b"DD2 "]
            for i in range(ds // 8):
                b = do + i * 8
                t = g.u16(b); x = g.u16(b + 2); y = g.u16(b + 4)
                ow = g.byte(b + 6); en = g.byte(b + 7)
                if t > 511 or x >= w * 32 or y >= h * 32:
                    continue
                dd.append((t, x, y, ow, en))
        ovl = 0
        oid = []
        for t, x, y, ow, en in dd:
            grp = None
            for m in range(n):
                if cv.u16(m * 52) == 1 and cv.u16(m * 52 + 12) == t:
                    grp = m
                    break
            if grp is None:
                continue
            fl = cv.u16(grp * 52 + 2)
            if fl & 0x1000 or fl & 0x2000:
                ovl += 1
                oid.append((cv.u16(grp * 52 + 4), fl))
        print("%-11s ts=%-8s %dx%d cv5n=%d rawOOB=%d newOOB=%d "
              "cv5types=%s mtxmtypes=%s dd2=%d ovl=%d" % (
                  mid, ts, w, h, n, bad_raw, bad_new,
                  dict(sorted(types.items())), dict(sorted(tcount.items())),
                  len(dd), ovl))
        if oid:
            print("            overlay ids:", sorted(set(oid))[:20])


main()

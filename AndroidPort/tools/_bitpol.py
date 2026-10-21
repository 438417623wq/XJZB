"""v2.44: is bit0 really the walkable bit in VF4?

pipeline_maps._walk_bitmap does `(f & 1)`.  The art test cannot tell bit0 from
bit1 apart (rock is flag 2, grass is flag 1/3 under either reading), so use a
property that is true by definition instead:

  * a RAMP tile (bit4) is walkable, and
  * a HIGH GROUND plateau tile (bit2) is walkable.

Whichever of bit0/bit1 those tiles carry is the walkable flag.
Bottleneck is used because it is the one map with ramps (288) and high ground
(26858); divide is included as the map under investigation.
"""
import os
import sys

import numpy as np

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

MAPS = [
    (r"maps\(2)Bottleneck.scm", "bottleneck"),
    (r"maps\(2)The Small Divide.scm", "divide"),
    (r"maps\(4)Blood Bath.scm", "bloodbath"),
]

BITS = [(0, "walk"), (1, "bit1"), (2, "high"), (3, "blkview"), (4, "ramp")]


def flags_of(scm):
    chk, gaps = pm.read_chk(os.path.join(pm.ROOT, scm))
    g, sec = pm.parse_chk(chk, gaps)
    off, _ = sec[b"DIM "]
    w, h = g.u16(off), g.u16(off + 2)
    eoff, _ = sec[b"ERA "]
    ts = pm.load_tileset(pm.TILESETS.get(g.byte(eoff), "platform"))
    moff, _ = sec[b"MTXM"]
    mt = np.array([g.u16(moff + 2 * i) for i in range(w * h)], dtype=np.uint32).reshape(h, w)
    grp = np.clip((mt & 0x7FF0) >> 4, 0, len(ts["cv5_tiles"]) - 1)
    var = mt & 0xF
    tiles = np.asarray(ts["cv5_tiles"], dtype=np.int64)
    vx4m = tiles[grp, var]
    fl = np.asarray(ts["vf4_flags"], dtype=np.int64)
    vx4m = np.where(vx4m >= len(fl), 0, vx4m)
    f = fl[vx4m].reshape(h, w, 4, 4)
    return f.transpose(0, 2, 1, 3).reshape(h * 4, w * 4)


def report(scm, name):
    f = flags_of(scm)
    print("== %s  %dx%d minitiles" % (name, f.shape[1], f.shape[0]))
    vals, cnts = np.unique(f, return_counts=True)
    order = np.argsort(-cnts)
    print("   distinct flag words (top 12):")
    for i in order[:12]:
        v = int(vals[i])
        bits = "".join(n if (v >> b) & 1 else "-" for b, n in BITS)
        print("     0x%04x %-9s %8d  %5.1f%%" % (v, bits, cnts[i], 100.0 * cnts[i] / f.size))
    for b, n in BITS:
        print("   bit%d %-8s set on %8d minitiles (%.1f%%)"
              % (b, n, int(((f >> b) & 1).sum()), 100.0 * ((f >> b) & 1).sum() / f.size))
    # decisive: what do ramp and high-ground tiles look like?
    for b, n in ((4, "ramp"), (2, "high")):
        m = ((f >> b) & 1).astype(bool)
        if not m.any():
            print("   no %s tiles" % n)
            continue
        vv, cc = np.unique(f[m], return_counts=True)
        o = np.argsort(-cc)
        print("   %s tiles carry: %s" % (n, ", ".join("0x%04x x%d" % (int(vv[i]), cc[i]) for i in o[:6])))
        print("      of those, bit0 set: %.1f%%   bit1 set: %.1f%%"
              % (100.0 * ((f[m] >> 0) & 1).mean(), 100.0 * ((f[m] >> 1) & 1).mean()))
    print()


for scm, name in MAPS:
    report(scm, name)

# connectivity of divide under each candidate reading
f = flags_of(r"maps\(2)The Small Divide.scm")
MW = f.shape[1]


def comps(walk):
    MH = walk.shape[0]
    comp = -np.ones((MH, MW), dtype=np.int32)
    cid = 0
    for sy in range(MH):
        for sx in range(MW):
            if comp[sy, sx] != -1 or not walk[sy, sx]:
                continue
            st = [(sx, sy)]
            comp[sy, sx] = cid
            while st:
                x, y = st.pop()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < MW and 0 <= ny < MH and walk[ny, nx] and comp[ny, nx] == -1:
                            comp[ny, nx] = cid
                            st.append((nx, ny))
            cid += 1
    return comp, cid


print("divide connectivity under each reading:")
for label, m in (("bit0", (f & 1).astype(bool)),
                 ("bit1", ((f >> 1) & 1).astype(bool)),
                 ("bit0|bit1", (((f & 1) | ((f >> 1) & 1))).astype(bool))):
    comp, n = comps(m)
    a = comp[240 // 8, 320 // 8]
    b = comp[1776 // 8, 1728 // 8]
    print("   %-10s walkable=%6d comps=%-4d player=%d enemy=%d SAME=%s"
          % (label, int(m.sum()), n, a, b, a == b))

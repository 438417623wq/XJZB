"""v2.44: is the MTXM group mask right?

_walk_bitmap reads the megatile group as (mt & 0x7FF0) >> 4, i.e. 11 bits, which
drops bit 15.  If The Small Divide has tiles with bit 15 set, every such tile
would be read as group-2048 and inherit a completely different megatile's VF4
flags -- which would invent walls out of nothing.

Print the raw MTXM histogram and rebuild the walk bitmap under both masks.
"""
import os
import sys

import numpy as np

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

SRC = r"maps\(2)The Small Divide.scm"
chk, gaps = pm.read_chk(os.path.join(pm.ROOT, SRC))
g, sec = pm.parse_chk(chk, gaps)
off, _ = sec[b"DIM "]
w, h = g.u16(off), g.u16(off + 2)
eoff, _ = sec[b"ERA "]
ts = pm.load_tileset(pm.TILESETS.get(g.byte(eoff), "platform"))
moff, _ = sec[b"MTXM"]
raw = np.array([g.u16(moff + 2 * i) for i in range(w * h)], dtype=np.uint32).reshape(h, w)
print("DIM %dx%d  n_cv5_groups=%d  n_vx4_refs=%d  n_vf4_flags=%d"
      % (w, h, len(ts["cv5_tiles"]), len(ts["vx4_refs"]), len(ts["vf4_flags"])))
print("raw MTXM  min=%d max=%d" % (raw.min(), raw.max()))
print("tiles with bit15 (0x8000) set: %d" % int((raw & 0x8000).sum()))
print("tiles with bit14 set:          %d" % int((raw & 0x4000).sum()))
vals, counts = np.unique(raw, return_counts=True)
top = sorted(zip(counts.tolist(), vals.tolist()), reverse=True)[:10]
print("top raw values:", [(int(v), int(c)) for c, v in top])
print("variant histogram (mt & 0xF):",
      [(int(v), int(c)) for v, c in zip(*np.unique(raw & 0xF, return_counts=True))])
print()

tiles = np.asarray(ts["cv5_tiles"], dtype=np.int64)
fl = np.asarray(ts["vf4_flags"], dtype=np.int64)

DIRS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]


def comps_of(walk):
    H, W = walk.shape
    comp = -np.ones((H, W), dtype=np.int32)
    cid = 0
    for sy in range(H):
        for sx in range(W):
            if comp[sy, sx] != -1 or not walk[sy, sx]:
                continue
            stk = [(sx, sy)]
            comp[sy, sx] = cid
            while stk:
                x, y = stk.pop()
                for dx, dy in DIRS:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and walk[ny, nx] and comp[ny, nx] == -1:
                        comp[ny, nx] = cid
                        stk.append((nx, ny))
            cid += 1
    return comp, cid


uoff, usize = sec[b"UNIT"]
st = []
for i in range(usize // 36):
    b = uoff + i * 36
    if g.u16(b + 8) == pm.START_ID:
        st.append((g.u16(b + 4) // 8, g.u16(b + 6) // 8))

for label, mask in (("0x7FF0 (11-bit, current)", 0x7FF0), ("0xFFF0 (12-bit)", 0xFFF0)):
    grp = (raw & mask) >> 4
    over = int((grp >= len(tiles)).sum())
    gcl = np.clip(grp, 0, len(tiles) - 1)
    vx4m = tiles[gcl, raw & 0xF]
    oob = int((vx4m >= len(fl)).sum())
    vx4m = np.where(vx4m >= len(fl), 0, vx4m)
    f = fl[vx4m].reshape(h, w, 4, 4)
    walk = (f & 1).astype(np.uint8).transpose(0, 2, 1, 3).reshape(h * 4, w * 4)
    comp, n = comps_of(walk)
    sa = comp[st[0][1], st[0][0]]
    sb = comp[st[1][1], st[1][0]]
    print("%-24s grp max=%4d  groups over n_cv5=%d  vx4 refs out of range=%d"
          % (label, int(grp.max()), over, oob))
    print("%-24s walkable=%d  comps=%d  start comps=%s/%s  SAME=%s"
          % ("", int(walk.sum()), n, sa, sb, sa == sb))
    print()

# what does each of the seven blocking cells look like raw?
print("the seven blocking cells, raw MTXM and both readings:")
for (mx, my) in [(189, 14), (109, 131), (110, 130), (111, 129),
                 (158, 106), (159, 107), (216, 164)]:
    tx, ty = mx // 4, my // 4
    r = int(raw[ty, tx])
    g11 = (r & 0x7FF0) >> 4
    g12 = (r & 0xFFF0) >> 4
    print("   minitile(%3d,%3d) tile(%2d,%2d) raw=0x%04X var=%d grp11=%d grp12=%d"
          % (mx, my, tx, ty, r, r & 0xF, g11, g12))

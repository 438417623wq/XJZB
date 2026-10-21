"""v2.44: find exactly WHERE _dilate(walk, 1) bridges divide's two landmasses.

If the bridging cell sits on flat grass/dirt art, the bake has a hairline crack
and the runtime bitmap (which is RAW, un-dilated) is wrong.  If it sits on cliff
rock, the wall is real and the dilation is what is wrong.

Also computes the true 8-connected crossing cost (the earlier _wall.py used
4-connected moves, which overstates the thickness of a diagonal wall).
"""
import os
import sys

import numpy as np

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

SRC = r"F:\KF\XJZB\maps\(2)The Small Divide.scm"
BAKED = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide\walk.bin.gz"
ART = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"

chk, gaps = pm.read_chk(SRC)
g, sec = pm.parse_chk(chk, gaps)
off, _ = sec[b"DIM "]
w, h = g.u16(off), g.u16(off + 2)
eoff, _ = sec[b"ERA "]
ts = pm.load_tileset(pm.TILESETS.get(g.byte(eoff), "platform"))
walk = pm._walk_bitmap(w, h, None, ts) if False else None

# rebuild walk exactly the way build_map does
moff, _ = sec[b"MTXM"]
mt = np.array([g.u16(moff + 2 * i) for i in range(w * h)], dtype=np.uint32).reshape(h, w)
grp = np.clip((mt & 0x7FF0) >> 4, 0, len(ts["cv5_tiles"]) - 1)
tiles = np.asarray(ts["cv5_tiles"], dtype=np.int64)
vx4m = tiles[grp, mt & 0xF]
fl = np.asarray(ts["vf4_flags"], dtype=np.int64)
vx4m = np.where(vx4m >= len(fl), 0, vx4m)
f = fl[vx4m].reshape(h, w, 4, 4)
walk = (f & 1).astype(np.uint8).transpose(0, 2, 1, 3).reshape(h * 4, w * 4)
MH, MW = walk.shape
print("map %dx%d tiles -> %dx%d minitiles  walkable=%d" % (w, h, MW, MH, int(walk.sum())))

# cross-check against the shipped bitmap
import gzip
shipped = np.frombuffer(gzip.open(BAKED, "rb").read(), dtype=np.uint8).reshape(MH, MW)
print("shipped bitmap differs from CHK rebuild in %d minitiles" % int((shipped != walk).sum()))

uoff, usize = sec[b"UNIT"]
starts = []
for i in range(usize // 36):
    b = uoff + i * 36
    if g.u16(b + 8) == pm.START_ID:
        starts.append((g.u16(b + 4) // 8, g.u16(b + 6) // 8))
print("starts (minitile) =", starts)


def label(wk):
    comp = -np.ones((MH, MW), dtype=np.int32)
    cid = 0
    for sy in range(MH):
        for sx in range(MW):
            if comp[sy, sx] != -1 or not wk[sy, sx]:
                continue
            stk = [(sx, sy)]
            comp[sy, sx] = cid
            while stk:
                x, y = stk.pop()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < MW and 0 <= ny < MH and wk[ny, nx] and comp[ny, nx] == -1:
                            comp[ny, nx] = cid
                            stk.append((nx, ny))
            cid += 1
    return comp, cid


comp, n = label(walk)
a = comp[starts[0][1], starts[0][0]]
b = comp[starts[1][1], starts[1][0]]
print("raw: comps=%d  player=%d enemy=%d SAME=%s" % (n, a, b, a == b))

# ---- true 8-connected crossing cost (0-1 BFS) -------------------------------
from collections import deque
INF = 10 ** 9
cost = np.full((MH, MW), INF, dtype=np.int32)
sx0, sy0 = starts[0]
cost[sy0, sx0] = 0
dq = deque([(sx0, sy0)])
while dq:
    x, y = dq.popleft()
    c = cost[y, x]
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if not (0 <= nx < MW and 0 <= ny < MH):
                continue
            nc = c + (0 if walk[ny, nx] else 1)
            if nc < cost[ny, nx]:
                cost[ny, nx] = nc
                if walk[ny, nx]:
                    dq.appendleft((nx, ny))
                else:
                    dq.append((nx, ny))
tx, ty = starts[1]
print("true 8-connected crossing cost (impassable cells stepped on) = %d" % cost[ty, tx])

# ---- where does dilate(1) bridge? ------------------------------------------
dil = walk.copy()
for dx in (-1, 0, 1):
    for dy in (-1, 0, 1):
        dil |= np.roll(np.roll(walk, dy, axis=0), dx, axis=1)
compD, nD = label(dil)
print("dilated: comps=%d player=%d enemy=%d SAME=%s"
      % (nD, compD[starts[0][1], starts[0][0]], compD[starts[1][1], starts[1][0]],
         compD[starts[0][1], starts[0][0]] == compD[starts[1][1], starts[1][0]]))

added = (dil > 0) & (walk == 0)
ys, xs = np.nonzero(added)
bridges = []
for x, y in zip(xs.tolist(), ys.tolist()):
    seen = {}
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < MW and 0 <= ny < MH and walk[ny, nx]:
                cidv = int(comp[ny, nx])
                seen.setdefault(cidv, []).append((nx, ny))
    if len(seen) >= 2:
        bridges.append((x, y, seen))
print("added cells that touch >=2 distinct RAW components: %d" % len(bridges))

for x, y, seen in bridges[:20]:
    print("   bridge minitile(%d,%d) worldpx=(%d,%d) links raw comps %s"
          % (x, y, x * 8, y * 8, sorted(seen.keys())))

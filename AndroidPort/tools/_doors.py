"""v2.44: the door graph.  For every pair of RAW walk components, find the
cheapest crossing (number of impassable minitiles stepped on) and where that
crossing is.  A door of cost 1 on flat grass is a bake crack; a door of cost 1
on cliff rock is a real narrow ledge; a door of cost >= 4 is a real wall.

Also samples the terrain art under every cost-1 door so we can tell which.
"""
import os
import sys
from collections import deque

import numpy as np
from PIL import Image

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

SRC = r"F:\KF\XJZB\maps\(2)The Small Divide.scm"
ART = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"

chk, gaps = pm.read_chk(SRC)
g, sec = pm.parse_chk(chk, gaps)
off, _ = sec[b"DIM "]
w, h = g.u16(off), g.u16(off + 2)
eoff, _ = sec[b"ERA "]
ts = pm.load_tileset(pm.TILESETS.get(g.byte(eoff), "platform"))
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
flags = f.transpose(0, 2, 1, 3).reshape(MH, MW)   # flag word per minitile

# ---- components ------------------------------------------------------------
comp = -np.ones((MH, MW), dtype=np.int32)
cid = 0
for sy in range(MH):
    for sx in range(MW):
        if comp[sy, sx] != -1 or not walk[sy, sx]:
            continue
        stk = [(sx, sy)]
        comp[sy, sx] = cid
        while stk:
            x, y = stk.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < MW and 0 <= ny < MH and walk[ny, nx] and comp[ny, nx] == -1:
                        comp[ny, nx] = cid
                        stk.append((nx, ny))
        cid += 1
sizes = [(int((comp == i).sum()), i) for i in range(cid)]
sizes.sort(reverse=True)
print("comps=%d  sizes=%s" % (cid, [s for s, _ in sizes[:8]]))

uoff, usize = sec[b"UNIT"]
starts = []
for i in range(usize // 36):
    b = uoff + i * 36
    if g.u16(b + 8) == pm.START_ID:
        starts.append((g.u16(b + 4) // 8, g.u16(b + 6) // 8))
pa = int(comp[starts[0][1], starts[0][0]])
pb = int(comp[starts[1][1], starts[1][0]])
print("player comp=%d  enemy comp=%d" % (pa, pb))

BIG = [i for s, i in sizes if s > 500]
print("big comps:", BIG)

# ---- 0-1 BFS from every big comp: cost field + parent ----------------------
INF = 10 ** 9
dirs = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]


def bfs(src_cid):
    cost = np.full((MH, MW), INF, dtype=np.int32)
    par = -np.ones((MH, MW, 2), dtype=np.int32)
    dq = deque()
    for y, x in zip(*np.nonzero(comp == src_cid)):
        cost[y, x] = 0
        dq.append((int(x), int(y)))
    while dq:
        x, y = dq.popleft()
        c = cost[y, x]
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < MW and 0 <= ny < MH):
                continue
            nc = c + (0 if walk[ny, nx] else 1)
            if nc < cost[ny, nx]:
                cost[ny, nx] = nc
                par[ny, nx, 0] = x
                par[ny, nx, 1] = y
                if walk[ny, nx]:
                    dq.appendleft((nx, ny))
                else:
                    dq.append((nx, ny))
    return cost, par


def trace(par, x, y, cost):
    """walk back the cheapest route and return the impassable cells on it"""
    cells = []
    cx, cy = x, y
    guard = 0
    while cost[cy, cx] > 0 and guard < 200000:
        guard += 1
        if not walk[cy, cx]:
            cells.append((cx, cy))
        px, py = int(par[cy, cx, 0]), int(par[cy, cx, 1])
        if px < 0:
            break
        cx, cy = px, py
    return list(reversed(cells))


print()
print("== door graph (cost = impassable minitiles stepped on)")
doors = []
for a in BIG:
    cost, par = bfs(a)
    for b in BIG:
        if b <= a:
            continue
        ys, xs = np.nonzero(comp == b)
        c = cost[ys, xs]
        k = int(c.argmin())
        best = int(c[k])
        bx, by = int(xs[k]), int(ys[k])
        doors.append((best, a, b, bx, by, cost, par))
        print("   comp%-2d -> comp%-2d  cost=%-3d  nearest cell minitile(%d,%d) worldpx=(%d,%d)"
              % (a, b, best, bx, by, bx * 8, by * 8))

# ---- the route the player->enemy crossing actually takes -------------------
cost, par = bfs(pa)
ys, xs = np.nonzero(comp == pb)
c = cost[ys, xs]
k = int(c.argmin())
route = trace(par, int(xs[k]), int(ys[k]), cost)
print()
print("player->enemy cheapest route steps on %d impassable minitiles:" % len(route))
for x, y in route:
    print("   minitile(%3d,%3d) tile(%2d,%2d) worldpx=(%4d,%4d) fw=0x%04x"
          % (x, y, x // 4, y // 4, x * 8, y * 8, int(flags[y, x])))

# ---- art under the cost-1 doors -------------------------------------------
sheet = Image.new("RGB", (w * 4 * 8, h * 4 * 8))
for cy in range(0, h * 4 // 64):
    for cx in range(0, w * 4 // 64):
        p = os.path.join(ART, "c_%d_%d.webp" % (cx, cy))
        if os.path.exists(p):
            sheet.paste(Image.open(p).convert("RGB"), (cx * 512, cy * 512))

print()
print("== art under every cost-1 door cell (mean RGB of the 8x8 world px)")
for best, a, b, bx, by, cost2, par2 in doors:
    if best != 1:
        continue
    # re-trace to get the actual single blocked cell
    cost3, par3 = bfs(a)
    ys2, xs2 = np.nonzero(comp == b)
    c3 = cost3[ys2, xs2]
    k3 = int(c3.argmin())
    r = trace(par3, int(xs2[k3]), int(ys2[k3]), cost3)
    for x, y in r:
        crop = sheet.crop((x * 8, y * 8, x * 8 + 8, y * 8 + 8))
        arr = np.asarray(crop, dtype=np.float32).reshape(-1, 3)
        print("   comp%-2d->comp%-2d minitile(%3d,%3d) worldpx=(%4d,%4d) fw=0x%04x mean=(%.1f,%.1f,%.1f)"
              % (a, b, x, y, x * 8, y * 8, int(flags[y, x]), *arr.mean(axis=0)))
        crop.resize((256, 256), Image.NEAREST).save(
            os.path.join(OUT, "_door_%d_%d_%d_%d.png" % (a, b, x, y)))
        sheet.crop((max(0, x * 8 - 128), max(0, y * 8 - 128),
                    x * 8 + 136, y * 8 + 136)).resize((528, 528), Image.LANCZOS).save(
            os.path.join(OUT, "_doorwide_%d_%d.png" % (x, y)))

"""v2.44: calibrate what a REAL separation costs.

For every map, list the walk components bigger than 500 minitiles and the
minimum number of impassable minitiles you must step on to get from one to
another (0-1 BFS, 8-connected).  A real cliff or river between two landmasses
should cost several cells; a hairline crack in the VF4 read costs exactly one.

Also render the art at divide's cost-1 doors with the minitile grid and the door
cell outlined, so we can see whether the mapmaker painted rock or a passage
there.
"""
import os
import sys
from collections import deque

import numpy as np
from PIL import Image

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

ART = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"

LEGACY = {
    "bloodbath": r"maps\(4)Blood Bath.scm",
    "bottleneck": r"maps\(2)Bottleneck.scm",
    "boxer": r"maps\(2)Boxer.scm",
    "hunters": r"maps\(8)The Hunters.scm",
    "darkcrystal": r"maps\(4)Dark Crystal.scm",
    "river": r"maps\(2)River Crossing.scm",
    "3kingdoms": r"maps\(3)Three Kingdoms.scm",
    "divide": r"maps\(2)The Small Divide.scm",
    "cyclone": r"maps\(4)Cyclone.scm",
    "volcanis": r"maps\(2)Volcanis.scm",
}
SRC = {m[1]: m[0] for m in pm.MAPS}
SRC.update(LEGACY)

ISLANDS = ["islandhop", "sapphireisles", "primevalisles", "archipelago",
           "steppingstones", "kakarukeys", "tripleteam", "alliedfortress",
           "doublediamond", "spacemadness", "hypothermia", "riverwar"]
MAINS = ["divide", "bloodbath", "bottleneck", "boxer", "hunters"]

DIRS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
INF = 10 ** 9


def build(mid):
    chk, gaps = pm.read_chk(os.path.join(pm.ROOT, SRC[mid]))
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
    uoff, usize = sec[b"UNIT"]
    st = []
    for i in range(usize // 36):
        b = uoff + i * 36
        if g.u16(b + 8) == pm.START_ID:
            st.append((g.u16(b + 4) // 8, g.u16(b + 6) // 8))
    return walk, st, (w, h)


def label(walk):
    MH, MW = walk.shape
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
                for dx, dy in DIRS:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < MW and 0 <= ny < MH and walk[ny, nx] and comp[ny, nx] == -1:
                        comp[ny, nx] = cid
                        stk.append((nx, ny))
            cid += 1
    return comp, cid


def bfs_from(comp, cid, walk):
    MH, MW = walk.shape
    cost = np.full((MH, MW), INF, dtype=np.int32)
    dq = deque()
    for y, x in zip(*np.nonzero(comp == cid)):
        cost[y, x] = 0
        dq.append((int(x), int(y)))
    while dq:
        x, y = dq.popleft()
        c = cost[y, x]
        for dx, dy in DIRS:
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
    return cost


print("== separation cost between every pair of components bigger than 500 cells")
print("   (cost = impassable minitiles stepped on; 1 = hairline, >=3 = real wall)")
for mid in MAINS + ISLANDS:
    walk, st, dims = build(mid)
    comp, n = label(walk)
    sizes = [(int((comp == i).sum()), i) for i in range(n)]
    big = sorted([s for s, _ in sizes if s > 500], reverse=True)
    ids = [i for s, i in sizes if s > 500]
    ids.sort(key=lambda i: -int((comp == i).sum()))
    costs = {}
    for i in ids:
        costs[i] = bfs_from(comp, i, walk)
    pairs = []
    for ai in range(len(ids)):
        for bi in range(ai + 1, len(ids)):
            a, b = ids[ai], ids[bi]
            ys, xs = np.nonzero(comp == b)
            c = int(costs[a][ys, xs].min())
            pairs.append((a, b, c))
    pa = pb = None
    if len(st) >= 2:
        pa = int(comp[st[0][1], st[0][0]])
        pb = int(comp[st[1][1], st[1][0]])
    psame = (pa == pb) if (pa is not None and pb is not None) else None
    mn = min([c for _, _, c in pairs]) if pairs else None
    print("   %-15s %-9s big=%-22s startComp=%s/%s SAME=%-5s minDoorCost=%s"
          % (mid, "%dx%d" % dims, big[:5], pa, pb, psame, mn))

# ---- art at divide's doors ------------------------------------------------
print()
print("== divide door art")
walk, st, (w, h) = build("divide")
comp, n = label(walk)
ids = [i for s, i in [(int((comp == i).sum()), i) for i in range(n)] if s > 500]
ids.sort(key=lambda i: -int((comp == i).sum()))

# every blocked cell whose walkable neighbours span two big components
doors = []
for y in range(walk.shape[0]):
    for x in range(walk.shape[1]):
        if walk[y, x]:
            continue
        seen = set()
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < walk.shape[1] and 0 <= ny < walk.shape[0] and walk[ny, nx]:
                c = int(comp[ny, nx])
                if (comp == c).sum() > 500:
                    seen.add(c)
        if len(seen) >= 2:
            doors.append((x, y, tuple(sorted(seen))))
print("   single blocked cells that would merge two big components: %d" % len(doors))
for x, y, s in doors:
    print("      minitile(%3d,%3d) tile(%2d,%2d) worldpx=(%4d,%4d) merges comps %s"
          % (x, y, x // 4, y // 4, x * 8, y * 8, s))

sheet = Image.new("RGB", (w * 4 * 8, h * 4 * 8))
for cy in range(0, h * 4 // 64):
    for cx in range(0, w * 4 // 64):
        p = os.path.join(ART, "c_%d_%d.webp" % (cx, cy))
        if os.path.exists(p):
            sheet.paste(Image.open(p).convert("RGB"), (cx * 512, cy * 512))

TINT = [(0, 255, 0), (0, 128, 255), (255, 255, 0), (255, 128, 0), (255, 0, 255)]
for x, y, s in doors[:6]:
    R = 20                       # minitiles around the door
    x0, y0 = max(0, x - R) * 8, max(0, y - R) * 8
    crop = sheet.crop((x0, y0, x0 + 2 * R * 8, y0 + 2 * R * 8)).convert("RGB")
    arr = np.asarray(crop, dtype=np.float32).copy()
    for j in range(2 * R):
        for i in range(2 * R):
            mx, my = max(0, x - R) + i, max(0, y - R) + j
            if my >= walk.shape[0] or mx >= walk.shape[1]:
                continue
            if not walk[my, mx]:
                arr[j * 8:(j + 1) * 8, i * 8:(i + 1) * 8] = \
                    arr[j * 8:(j + 1) * 8, i * 8:(i + 1) * 8] * 0.45 + \
                    np.array([255, 0, 0], dtype=np.float32) * 0.55
            else:
                c = int(comp[my, mx])
                if c in TINT:
                    t = np.array(TINT[c], dtype=np.float32)
                    arr[j * 8:(j + 1) * 8, i * 8:(i + 1) * 8] = \
                        arr[j * 8:(j + 1) * 8, i * 8:(i + 1) * 8] * 0.72 + t * 0.28
    # grid
    for j in range(2 * R + 1):
        arr[min(j * 8, arr.shape[0] - 1), :, :] = arr[min(j * 8, arr.shape[0] - 1), :, :] * 0.5
    for i in range(2 * R + 1):
        arr[:, min(i * 8, arr.shape[1] - 1), :] = arr[:, min(i * 8, arr.shape[1] - 1), :] * 0.5
    # door cell outline
    di, dj = x - max(0, x - R), y - max(0, y - R)
    for k in range(8):
        arr[dj * 8, di * 8 + k] = [255, 0, 255]
        arr[dj * 8 + 7, di * 8 + k] = [255, 0, 255]
        arr[dj * 8 + k, di * 8] = [255, 0, 255]
        arr[dj * 8 + k, di * 8 + 7] = [255, 0, 255]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(
        os.path.join(OUT, "_doorart_%d_%d.png" % (x, y)))
    print("      wrote out/_doorart_%d_%d.png  (%dx%d minitiles, 3x)" % (x, y, 2 * R, 2 * R))

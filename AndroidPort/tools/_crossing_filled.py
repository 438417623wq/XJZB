"""v2.44: which crossing does the pipeline's own _fill_enclosed use?

_crossing.py computed the cheapest route on the RAW shipped bitmap and found 7
blocked cells. But pipeline_maps.connectivity() runs _fill_enclosed first and
then calls the map connected -- so on the FILLED bitmap there must be a cheaper
route. If that route runs through cells _fill_enclosed flipped, those cells are
the "damaged repack leaves single-minitile holes in the VF4 read" the pipeline
header documents, and the raw wall is an artifact.

Print the filled-bitmap route, mark which of its cells are blocked on the raw
bitmap, and report each one's art neighbourhood so it can be eyeballed.
"""
import gzip
import os
from collections import deque

import numpy as np
from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
MID = "divide"
CS = 512


def load(mid):
    with gzip.open(os.path.join(ASSETS, mid, "walk.bin.gz"), "rb") as f:
        raw = f.read()
    meta = {}
    with open(os.path.join(ASSETS, mid, "meta.txt"), "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                meta.setdefault(k, []).append(v)
    w, h = int(meta["w"][0]), int(meta["h"][0])
    starts = [[int(v) for v in s.split(",")] for s in meta["start"]]
    return np.frombuffer(raw, dtype=np.uint8).reshape(h * 4, w * 4), starts, w, h


def fill_enclosed(walk):
    mh, mw = walk.shape
    seen = np.zeros((mh, mw), dtype=bool)
    dq = deque()
    for x in range(mw):
        for y in (0, mh - 1):
            if not walk[y, x] and not seen[y, x]:
                seen[y, x] = True
                dq.append((y, x))
    for y in range(mh):
        for x in (0, mw - 1):
            if not walk[y, x] and not seen[y, x]:
                seen[y, x] = True
                dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < mh and 0 <= xx < mw and not walk[yy, xx] and not seen[yy, xx]:
                seen[yy, xx] = True
                dq.append((yy, xx))
    out = walk.copy()
    out[~seen] = 1
    return out


def snap(walk, px, py):
    mx, my = int(px) // 8, int(py) // 8
    mh, mw = walk.shape
    for r in range(0, 64):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                x, y = mx + dx, my + dy
                if 0 <= x < mw and 0 <= y < mh and walk[y, x]:
                    return (y, x)
    return None


def route(walk, a, b):
    mh, mw = walk.shape
    INF = 1 << 30
    cost = np.full((mh, mw), INF, dtype=np.int32)
    par = {}
    cost[a] = 0
    q = deque([a])
    while q:
        y, x = q.popleft()
        c = cost[y, x]
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                yy, xx = y + dy, x + dx
                if yy < 0 or xx < 0 or yy >= mh or xx >= mw:
                    continue
                nc = c + (0 if walk[yy, xx] else 1)
                if nc < cost[yy, xx]:
                    cost[yy, xx] = nc
                    par[(yy, xx)] = (y, x)
                    (q.appendleft if walk[yy, xx] else q.append)((yy, xx))
    path = []
    cur = b
    while cur != a:
        path.append(cur)
        cur = par[cur]
    path.append(a)
    path.reverse()
    return path, cost[b]


walk, starts, w, h = load(MID)
filled = fill_enclosed(walk)
a = snap(walk, starts[0][0], starts[0][1])
b = snap(walk, starts[1][0], starts[1][1])

for label, wk in (("RAW", walk), ("FILLED", filled)):
    path, cost = route(wk, a, b)
    blocked = [(y, x) for (y, x) in path if not walk[y, x]]
    print("%-6s cheapest cost=%d route len=%d  blocked-on-raw cells=%d %s"
          % (label, cost, len(path), len(blocked), blocked[:20]))

path_f, _ = route(filled, a, b)
blocked_f = [(y, x) for (y, x) in path_f if not walk[y, x]]
print("\nFILLED route passes through these raw-blocked cells:")
for (y, x) in blocked_f:
    flipped = bool(filled[y, x] and not walk[y, x])
    print("   minitile(%3d,%3d) tile(%2d,%2d) worldpx=(%4d,%4d) was_filled=%s"
          % (x, y, x // 4, y // 4, x * 8, y * 8, flipped))

# is the whole divide bridged by filled pockets, or just one spot?
ys, xs = np.nonzero(filled != walk)
print("\n_fill_enclosed flipped %d cells" % len(ys))
print("   of those, how many lie within 6 minitiles of the FILLED route: %d"
      % sum(1 for (y, x) in zip(ys, xs)
            if any(abs(y - py) <= 6 and abs(x - px) <= 6 for (py, px) in blocked_f)))

# render the FILLED route's blocked cells over the art
if blocked_f:
    cy, cx = blocked_f[len(blocked_f) // 2]
    r = 12
    x0, y0 = max(0, (cx - r) * 8), max(0, (cy - r) * 8)
    x1, y1 = min(w * 32, (cx + r) * 8), min(h * 32, (cy + r) * 8)
    base = Image.new("RGB", (x1 - x0, y1 - y0), (0, 0, 0))
    for ccy in range(y0 // CS, (y1 - 1) // CS + 1):
        for ccx in range(x0 // CS, (x1 - 1) // CS + 1):
            p = os.path.join(ASSETS, MID, "c_%d_%d.webp" % (ccx, ccy))
            if os.path.exists(p):
                base.paste(Image.open(p).convert("RGB"), (ccx * CS - x0, ccy * CS - y0))
    sc = 8
    big = base.resize(((x1 - x0) * sc, (y1 - y0) * sc), Image.NEAREST)
    px = big.load()
    for (y, x) in blocked_f:
        bx, by = (x * 8 - x0) * sc, (y * 8 - y0) * sc
        for dy in range(8 * sc):
            for dx in range(8 * sc):
                if 0 <= bx + dx < big.size[0] and 0 <= by + dy < big.size[1]:
                    px[bx + dx, by + dy] = (255, 0, 0)
    p = os.path.join(OUT, "_divide_filled_route.jpg")
    big.save(p, quality=90)
    print("saved %s  (red = cell the filled route crosses that raw says is blocked)" % p)

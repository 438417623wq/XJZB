"""v2.44: locate divide's cheapest crossing between the two start components.

_wall.py says the two starts are 7 impassable minitiles apart (56 world px),
which is far too thin to be a river and suspiciously like a ramp the VF4 read
closed. Two things to settle before calling it a bug:

  1. WHERE is that crossing, and what does the terrain look like there?
  2. How much does pipeline_maps._fill_enclosed actually flip on divide? Its
     connectivity() gate answers "connected" (island=0 in meta.json) even though
     the raw shipped bitmap says otherwise -- so one of the two is lying.
"""
import gzip
import os
from collections import deque

import numpy as np
from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
MID = "divide"


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
    starts = [[int(x) for x in s.split(",")] for s in meta["start"]]
    return np.frombuffer(raw, dtype=np.uint8).reshape(h * 4, w * 4), starts, w, h


def elev_of(mid, shape):
    p = os.path.join(ASSETS, mid, "elev.bin.gz")
    with gzip.open(p, "rb") as f:
        raw = f.read()
    return np.frombuffer(raw, dtype=np.uint8).reshape(shape)


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


def cheapest_route(walk, a, b):
    """0-1 BFS with parent tracking: returns the path and its impassable cost."""
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
                    if walk[yy, xx]:
                        q.appendleft((yy, xx))
                    else:
                        q.append((yy, xx))
    path = []
    cur = b
    while cur != a:
        path.append(cur)
        cur = par[cur]
    path.append(a)
    path.reverse()
    return path, cost[b]


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


walk, starts, w, h = load(MID)
elev = elev_of(MID, walk.shape)
a = snap(walk, starts[0][0], starts[0][1])
b = snap(walk, starts[1][0], starts[1][1])
print("starts px=%s  snapped minitiles A=%s B=%s" % (starts, a, b))

path, cost = cheapest_route(walk, a, b)
print("cheapest crossing cost = %d impassable minitiles, route length %d" % (cost, len(path)))
crossings = [(y, x) for (y, x) in path if not walk[y, x]]
print("blocked minitiles on the route: %s" % crossings)
for (y, x) in crossings:
    print("   minitile(%d,%d) tile(%d,%d) elev=%d  worldpx=(%d,%d)"
          % (x, y, x // 4, y // 4, elev[y, x], x * 8, y * 8))

flipped = fill_enclosed(walk)
n_flip = int((flipped != walk).sum())
print("_fill_enclosed flips %d minitiles on %s (of %d)" % (n_flip, MID, walk.size))

# where are the flipped cells? bounding box + whether the crossing is among them
ys, xs = np.nonzero(flipped != walk)
if len(ys):
    print("   flipped bbox rows %d..%d cols %d..%d" % (ys.min(), ys.max(), xs.min(), xs.max()))
    print("   crossing cells flipped? %s"
          % [bool(flipped[y, x]) for (y, x) in crossings])

# render a zoomed crop around the crossing so the terrain is inspectable
if crossings:
    cy, cx = crossings[len(crossings) // 2]
    r = 40
    y0, y1 = max(0, cy - r), min(walk.shape[0], cy + r)
    x0, x1 = max(0, cx - r), min(walk.shape[1], cx + r)
    crop = walk[y0:y1, x0:x1]
    ecrop = elev[y0:y1, x0:x1]
    im = Image.new("RGB", (x1 - x0, y1 - y0))
    px = im.load()
    for yy in range(y1 - y0):
        for xx in range(x1 - x0):
            if crop[yy, xx]:
                px[xx, yy] = (60 + 60 * int(ecrop[yy, xx]), 120, 60)
            else:
                px[xx, yy] = (20, 20, 20)
    for (y, x) in crossings:
        if y0 <= y < y1 and x0 <= x < x1:
            px[x - x0, y - y0] = (255, 0, 0)
    im = im.resize(((x1 - x0) * 8, (y1 - y0) * 8), Image.NEAREST)
    p = os.path.join(OUT, "_divide_crossing.png")
    im.save(p)
    print("crop saved %s  (green=walkable by elev, red=blocked crossing cell)" % p)

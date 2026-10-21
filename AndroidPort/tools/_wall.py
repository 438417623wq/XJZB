"""v2.44: how thick is the wall between divide's two walk components?

_conn.py found the player CC (320,240) and the enemy hatchery (1728,1776) in two
different components of walk.bin.gz, yet divide's meta.json says island=0
(connected). pipeline_maps.connectivity() answers a *different* question: it
fills enclosed holes and then square-dilates by GATE_DILATE before flooding. So
the two answers can disagree, and which one is right decides whether this is a
bake defect (a one-minitile seam that should be walkable) or the real map (a
river you genuinely cannot cross on foot).

Measure it: BFS outward from component A treating every minitile as passable,
and report the minimum number of NON-walkable minitiles a path has to cross to
reach component B. 1 means a hairline seam.
"""
import gzip
import os
from collections import deque

import numpy as np

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"


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
    return np.frombuffer(raw, dtype=np.uint8).reshape(h * 4, w * 4), starts


def label_components(walk):
    mh, mw = walk.shape
    lab = np.full((mh, mw), -1, dtype=np.int32)
    comp = 0
    sizes = []
    for sy in range(mh):
        for sx in range(mw):
            if walk[sy, sx] == 0 or lab[sy, sx] != -1:
                continue
            q = deque([(sy, sx)])
            lab[sy, sx] = comp
            n = 0
            while q:
                y, x = q.popleft()
                n += 1
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < mh and 0 <= xx < mw and walk[yy, xx] and lab[yy, xx] == -1:
                            lab[yy, xx] = comp
                            q.append((yy, xx))
            sizes.append(n)
            comp += 1
    return lab, sizes


def snap(lab, walk, px, py):
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


def wall_thickness(walk, a, b):
    """Fewest impassable minitiles any 8-connected route from a to b must cross."""
    mh, mw = walk.shape
    INF = 1 << 30
    cost = np.full((mh, mw), INF, dtype=np.int32)
    ay, ax = a
    cost[ay, ax] = 0
    q = deque([(ay, ax)])
    while q:
        y, x = q.popleft()
        c = cost[y, x]
        if (y, x) == b:
            break
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
                    # 0-1 BFS: cheap edges go to the front
                    if walk[yy, xx]:
                        q.appendleft((yy, xx))
                    else:
                        q.append((yy, xx))
    return cost[b]


def dilate(walk, r):
    out = walk.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= np.roll(np.roll(walk, dy, axis=0), dx, axis=1)
    return out


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
    out[~seen] = True
    return out


for mid in ["divide", "bloodbath", "wasteland", "bottleneck"]:
    walk, starts = load(mid)
    lab, sizes = label_components(walk)
    pts = [snap(lab, walk, s[0], s[1]) for s in starts]
    ca = lab[pts[0]] if pts[0] else -1
    cb = lab[pts[1]] if pts[1] else -1
    th = wall_thickness(walk, pts[0], pts[1]) if pts[0] and pts[1] else -1
    fe = fill_enclosed(walk)
    d1 = dilate(fe, 1)
    lab2, _ = label_components(d1)
    p2 = [snap(lab2, d1, s[0], s[1]) for s in starts]
    conn_d1 = len(set(lab2[p] for p in p2 if p)) == 1
    print("%-12s raw comps=%d  A=%d B=%d  wallThickness=%d  |  fill+dilate1 connected=%s"
          % (mid, len(sizes), ca, cb, th, conn_d1))

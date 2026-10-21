"""Batch D regression probe: run5 (first GameDesktop run on the CORRECTED
terrain) crashes because the player is wiped -- no SCVs left at
GameDesktop.java:105. run4 predates the map regeneration, so the "52 PASS
after the terrain fix" claim was never actually re-verified.

Question: did the corrected walk map wall the player in? Flood-fill from the
player start and compare the reachable area against the mineral line.
"""
import gzip
import os
import sys
from collections import Counter, deque

ROOT = r"F:\KF\XJZB"
MAPS = os.path.join(ROOT, r"AndroidPort\app\app\src\main\assets\maps")


def load(map_id):
    d = os.path.join(MAPS, map_id)
    with gzip.open(os.path.join(d, "walk.bin.gz"), "rb") as f:
        walk = f.read()
    meta, starts, units = {}, [], []
    with open(os.path.join(d, "meta.txt"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            k, _, v = line.partition("=")
            if k == "start":
                starts.append(tuple(int(x) for x in v.split(",")))
            elif k == "unit":
                units.append([int(x) for x in v.split(",")])
            else:
                meta[k] = v
    return walk, int(meta["w"]), int(meta["h"]), starts, units


def flood(walk, mw, mh, sx, sy):
    """8px minitiles; a unit is 32px so only count minitiles whose 4x4 block is
    fully open, which is what the pathfinder effectively needs."""
    def open4(mx, my):
        for dy in range(4):
            for dx in range(4):
                x, y = mx * 4 + dx, my * 4 + dy
                if not (0 <= x < mw and 0 <= y < mh):
                    return False
                if not walk[y * mw + x]:
                    return False
        return True

    start = (sx // 32, sy // 32)
    if not open4(*start):
        return None, start
    seen = {start}
    q = deque([start])
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (cx + dx, cy + dy)
            if n in seen:
                continue
            if not (0 <= n[0] < mw // 4 and 0 <= n[1] < mh // 4):
                continue
            if open4(*n):
                seen.add(n)
                q.append(n)
    return seen, start


for map_id in sys.argv[1:] or ["bloodbath"]:
    walk, w, h, starts, units = load(map_id)
    mw, mh = w * 4, h * 4
    hist = Counter(walk)
    print("== %s %dx%d  walk histogram=%s" % (map_id, w, h, dict(hist.most_common(5))))
    tot_tiles = (mw // 4) * (mh // 4)
    for i, (sx, sy) in enumerate(starts):
        seen, st = flood(walk, mw, mh, sx, sy)
        if seen is None:
            print("   start%d (%d,%d) tile=%s BLOCKED" % (i, sx, sy, st))
            continue
        print("   start%d (%d,%d) tile=%s reachable=%d/%d tiles (%.1f%%)"
              % (i, sx, sy, st, len(seen), tot_tiles, 100.0 * len(seen) / tot_tiles))
    # where are the player's (team 0) units relative to start0's region?
    seen0, _ = flood(walk, mw, mh, starts[0][0], starts[0][1])
    if seen0:
        out = 0
        for u in units:
            _t, ux, uy, _a, _b, team = u
            if team != 0:
                continue
            if (ux // 32, uy // 32) not in seen0:
                out += 1
                if out <= 10:
                    print("   team0 unit at (%d,%d) tile=(%d,%d) OUTSIDE start0 region"
                          % (ux, uy, ux // 32, uy // 32))
        print("   team0 units total=%d outside start0 region=%d"
              % (sum(1 for u in units if u[5] == 0), out))

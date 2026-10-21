"""Batch D regression probe: the player's SCVs never mine on the regenerated
maps (minerals frozen at 432 for 240 s, then the base falls). Flood-fill says
the starts are fine, so check whether the MINERAL FIELDS are still reachable.

meta.txt unit rows are `unit=<kind>,<x>,<y>,<variant>,<unused>,<team>`;
kind 1 = mineral, kind 2 = geyser. pipeline_maps.py writes them straight from
the CHK UNIT section, so this also double-checks the batch-D rewrite did not
move resource positions.
"""
import gzip
import os
import sys
from collections import deque

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


def region(walk, mw, mh, sx, sy):
    def open4(mx, my):
        for dy in range(4):
            for dx in range(4):
                x, y = mx * 4 + dx, my * 4 + dy
                if not (0 <= x < mw and 0 <= y < mh) or not walk[y * mw + x]:
                    return False
        return True

    start = (sx // 32, sy // 32)
    if not open4(*start):
        return None
    seen = {start}
    q = deque([start])
    while q:
        cx, cy = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (cx + dx, cy + dy)
            if n in seen or not (0 <= n[0] < mw // 4 and 0 <= n[1] < mh // 4):
                continue
            if open4(*n):
                seen.add(n)
                q.append(n)
    return seen


for map_id in sys.argv[1:] or ["bloodbath"]:
    walk, w, h, starts, units = load(map_id)
    mw, mh = w * 4, h * 4
    print("== %s %dx%d" % (map_id, w, h))
    regs = []
    for i, (sx, sy) in enumerate(starts):
        r = region(walk, mw, mh, sx, sy)
        regs.append(r)
        print("   start%d (%4d,%4d) region=%s" % (i, sx, sy, len(r) if r else "BLOCKED"))
    res = [u for u in units if u[0] in (1, 2)]
    print("   resources=%d" % len(res))
    for u in res[:20]:
        kind, x, y = u[0], u[1], u[2]
        t = (x // 32, y // 32)
        own = [i for i, r in enumerate(regs) if r and t in r]
        print("     %s (%4d,%4d) tile=%-9s in-region=%s"
              % ("mineral" if kind == 1 else "geyser ", x, y, t, own or "UNREACHABLE"))
    # how many minerals sit in the player's own region?
    r0 = regs[0]
    if r0:
        n0 = sum(1 for u in res if (u[1] // 32, u[2] // 32) in r0)
        print("   resources in start0 region = %d/%d" % (n0, len(res)))

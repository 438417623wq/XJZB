"""v2.44: for every map, how much does dilate(1) buy?

Only needs the two start components, so it is two BFS runs per map instead of
one per component.  For each map print:
  raw SAME          -- are the starts connected with NO dilation
  door cost         -- impassable minitiles you must step on (0-1 BFS)
  dilate1 SAME      -- the bake's gate verdict (GATE_DILATE = 1)
  filled SAME       -- _fill_enclosed only, still no dilation
"""
import os
import sys
from collections import deque

import numpy as np

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

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
DIRS = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
INF = 10 ** 9


def snap(walk, x, y, r=40):
    """Chebyshev ring search for the nearest walkable cell (same as connectivity())."""
    if 0 <= x < walk.shape[1] and 0 <= y < walk.shape[0] and walk[y, x]:
        return (x, y)
    for rad in range(1, r):
        for dy in range(-rad, rad + 1):
            for dx in range(-rad, rad + 1):
                if max(abs(dx), abs(dy)) != rad:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < walk.shape[1] and 0 <= ny < walk.shape[0] and walk[ny, nx]:
                    return (nx, ny)
    return None


def same(walk, a, b):
    """8-connected flood from a, see if b is reached."""
    if a is None or b is None:
        return None
    seen = np.zeros(walk.shape, dtype=bool)
    dq = deque([a])
    seen[a[1], a[0]] = True
    while dq:
        x, y = dq.popleft()
        if (x, y) == b:
            return True
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < walk.shape[1] and 0 <= ny < walk.shape[0] \
                    and walk[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                dq.append((nx, ny))
    return False


def doorcost(walk, a, b):
    """0-1 BFS from a; min impassable cells stepped on to stand on b."""
    H, W = walk.shape
    cost = np.full((H, W), INF, dtype=np.int32)
    cost[a[1], a[0]] = 0
    dq = deque([a])
    while dq:
        x, y = dq.popleft()
        c = cost[y, x]
        if (x, y) == b:
            return c
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < W and 0 <= ny < H):
                continue
            nc = c + (0 if walk[ny, nx] else 1)
            if nc < cost[ny, nx]:
                cost[ny, nx] = nc
                if walk[ny, nx]:
                    dq.appendleft((nx, ny))
                else:
                    dq.append((nx, ny))
    return int(cost[b[1], b[0]])


print("map             dims     rawSAME door dilate1 filled  (expect)")
for mid in ISLANDS + ["divide"] + [m[1] for m in pm.MAPS if m[1] not in ISLANDS] + \
        [k for k in LEGACY if k not in ISLANDS]:
    if mid not in SRC:
        continue
    try:
        chk, gaps = pm.read_chk(os.path.join(pm.ROOT, SRC[mid]))
        g, sec = pm.parse_chk(chk, gaps)
        off, _ = sec[b"DIM "]
        w, h = g.u16(off), g.u16(off + 2)
        eoff, _ = sec[b"ERA "]
        ts = pm.load_tileset(pm.TILESETS.get(g.byte(eoff), "platform"))
        moff, _ = sec[b"MTXM"]
        mt = np.array([g.u16(moff + 2 * i) for i in range(w * h)],
                      dtype=np.uint32).reshape(h, w)
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
        if len(st) < 2:
            continue
        sa, sb = snap(walk, *st[0]), snap(walk, *st[1])
        raw = same(walk, sa, sb)
        dc = doorcost(walk, sa, sb) if raw is False else 0
        dil = same(pm._dilate(walk, 1), sa, sb)
        fil = same(pm._fill_enclosed(walk), sa, sb)
        exp = "SPLIT" if mid in ISLANDS else ("SPLIT" if mid == "divide" else "SAME")
        print("%-15s %-8s %-7s %-4s %-7s %-7s %s"
              % (mid, "%dx%d" % (w, h), raw, dc, dil, fil, exp))
    except Exception as exc:                                   # noqa: BLE001
        print("%-15s ERROR %s: %s" % (mid, type(exc).__name__, exc))

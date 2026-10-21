# v2.44: how many A* expansions does a base-to-base path actually need?
#
# Game.findPath gives up after a fixed 60000 expansions. On a 64x64 map that is
# more than the whole minitile grid, so it never bites; on 128x128 it is a
# quarter of the grid, and a path that has to feel its way around cliffs can
# exceed it and come back null -- which the AI reads as "no path" and the wave
# then sits still forever. This counts what each mission actually needs, using
# the same grid, the same 8-neighbour rule and the same corner test as Game.
import gzip
import heapq
import json
import os

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
DX = (1, -1, 0, 0, 1, 1, -1, -1)
DY = (0, 0, 1, -1, 1, -1, 1, -1)


def load(map_id):
    d = os.path.join(ASSETS, "maps", map_id)
    meta = {}
    for line in open(os.path.join(d, "meta.txt"), encoding="utf-8", errors="replace"):
        if "=" in line:
            k, v = line.split("=", 1)
            meta.setdefault(k.strip(), []).append(v.strip())
    w = int(meta["w"][0])
    h = int(meta["h"][0])
    for name in ("walk.bin.gz", "walk.gz", "walk.bin"):
        p = os.path.join(d, name)
        if os.path.exists(p):
            raw = gzip.decompress(open(p, "rb").read()) if name.endswith(".gz") \
                else open(p, "rb").read()
            return w, h, raw
    return w, h, None


def snap(walk, W, H, x, y, maxr=24):
    for r in range(0, maxr + 1):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                X, Y = x + dx, y + dy
                if 0 <= X < W and 0 <= Y < H and walk[Y * W + X]:
                    return X, Y
    return None


def astar(walk, W, H, sx, sy, gx, gy, cap):
    start, goal = sy * W + sx, gy * W + gx
    gs = {start: 0.0}
    heap = [(0.0, start)]
    closed = set()
    expansions = 0
    while heap and expansions < cap:
        _, cur = heapq.heappop(heap)
        if cur in closed:
            continue
        closed.add(cur)
        expansions += 1
        if cur == goal:
            return expansions, True
        cx, cy = cur % W, cur // W
        for d in range(8):
            nx, ny = cx + DX[d], cy + DY[d]
            if not (0 <= nx < W and 0 <= ny < H) or not walk[ny * W + nx]:
                continue
            if d >= 4:
                if not walk[cy * W + (cx + DX[d])] or not walk[(cy + DY[d]) * W + cx]:
                    continue
            ni = ny * W + nx
            if ni in closed:
                continue
            ng = gs[cur] + (1.4142 if d >= 4 else 1.0)
            if ni not in gs or ng < gs[ni]:
                gs[ni] = ng
                hx, hy = abs(nx - gx), abs(ny - gy)
                hh = (hx + hy) + (1.4142 - 2.0) * min(hx, hy)
                heapq.heappush(heap, (ng + hh, ni))
    return expansions, False


rows = []
for line in open(os.path.join(ASSETS, "missions", "index.txt"), encoding="utf-8"):
    p = [x.strip() for x in line.strip().split("|")]
    if len(p) >= 3 and p[0]:
        rows.append(p[0])

seen = {}
worst = 0
for mid in rows:
    j = json.load(open(os.path.join(ASSETS, "missions", mid + ".json"), encoding="utf-8"))
    map_id = j["map"]
    if map_id in seen:
        continue
    seen[map_id] = True
    w, h, raw = load(map_id)
    if raw is None:
        continue
    W, H = w * 4, h * 4
    walk = raw
    hall = None
    for u in j.get("startUnits", []):
        if u.get("team", 0) == 0 and u["type"] in ("cc", "hatchery", "nexus"):
            hall = u
            break
    foe = None
    for u in j.get("startUnits", []):
        if u.get("team", 0) == 1 and u["type"] in ("hatchery", "nexus", "cc"):
            foe = u
            break
    if hall is None:
        continue
    a = snap(walk, W, H, hall["x"] // 8, hall["y"] // 8)
    if a is None:
        print("%-5s %-14s player hall has no walkable minitile" % (mid, map_id))
        continue
    targets = []
    if foe:
        b = snap(walk, W, H, foe["x"] // 8, foe["y"] // 8)
        if b:
            targets.append(("enemy hall (%d,%d)" % (foe["x"], foe["y"]), b))
    for e in j.get("events", []):
        if e.get("action") == "wave" and e.get("from"):
            fr = e["from"]
            b = snap(walk, W, H, fr[0] // 8, fr[1] // 8)
            if b:
                targets.append(("wave from (%d,%d)" % (fr[0], fr[1]), b))
    for label, b in targets:
        # AI walks from its own spot to the PLAYER, so search the other way too
        n1, ok1 = astar(walk, W, H, a[0], a[1], b[0], b[1], 10 ** 7)
        n2, ok2 = astar(walk, W, H, b[0], b[1], a[0], a[1], 10 ** 7)
        n = max(n1, n2)
        worst = max(worst, n)
        print("%-5s %-14s %-24s grid=%dx%d  expansions=%7d found=%s  %s"
              % (mid, map_id, label, W, H, n, ok1 and ok2,
                 "OVER 60000 CAP" if n > 60000 else ""))
print("worst expansions across all mission targets: %d" % worst)

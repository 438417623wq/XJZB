# v2.44: how much does a heuristic weight cut A* expansions?
#
# Game.findPath uses a plain admissible heuristic (octile distance). On an open
# grid that leaves thousands of equally-good frontier nodes, so the search
# fans out and a base-to-base path can expand 100k+ cells -- past the 60000
# cap, which is why five missions' AI never arrives. Weighting the heuristic
# (weighted A*) collapses that frontier for a path a few percent longer, which
# no player can see. This measures the trade on the real maps.
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
    w, h = int(meta["w"][0]), int(meta["h"][0])
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


def astar(walk, W, H, sx, sy, gx, gy, wgt, tie):
    start, goal = sy * W + sx, gy * W + gx
    gs = {start: 0.0}
    heap = [(octile(sx, sy, gx, gy), 0.0, start)]
    closed = set()
    expansions = 0
    while heap:
        f, gcur, cur = heapq.heappop(heap)
        if cur in closed:
            continue
        closed.add(cur)
        expansions += 1
        if cur == goal:
            return expansions, gcur
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
                h = octile(nx, ny, gx, gy)
                # f = g + w*h, then break f-ties toward the *deeper* node
                # (subtract g). On an open axis-aligned rectangle every cell
                # between start and goal has the same f, so without this the
                # search floods the whole rectangle: that is where the
                # six-figure expansion counts come from, not from the weight.
                key = ng + wgt * h - tie * ng
                heapq.heappush(heap, (key, ng, ni))
    return expansions, None


def octile(x, y, gx, gy):
    dx, dy = abs(x - gx), abs(y - gy)
    return (dx + dy) + (1.4142 - 2.0) * min(dx, dy)


CASES = [("plain w=1.00", 1.00, 0.0),
         ("w=1.15 tie=.1", 1.15, 0.1),
         ("w=1.50 tie=.1", 1.50, 0.1),
         ("w=2.00 tie=.1", 2.00, 0.1),
         ("w=3.00 tie=.1", 3.00, 0.1),
         ("w=5.00 tie=.1", 5.00, 0.1)]

rows = [l.strip().split("|")[0].strip()
        for l in open(os.path.join(ASSETS, "missions", "index.txt"), encoding="utf-8")
        if l.strip()]

for mid in rows:
    j = json.load(open(os.path.join(ASSETS, "missions", mid + ".json"), encoding="utf-8"))
    map_id = j["map"]
    w, h, raw = load(map_id)
    if raw is None:
        continue
    W, H = w * 4, h * 4
    a = None
    for u in j.get("startUnits", []):
        if u.get("team", 0) == 0 and u["type"] in ("cc", "hatchery", "nexus"):
            a = snap(raw, W, H, u["x"] // 8, u["y"] // 8)
            break
    b = None
    for u in j.get("startUnits", []):
        if u.get("team", 0) == 1 and u["type"] in ("hatchery", "nexus", "cc"):
            b = snap(raw, W, H, u["x"] // 8, u["y"] // 8)
            break
    if a is None or b is None:
        continue
    print("== %s %s grid=%dx%d" % (mid, map_id, W, H))
    for label, wgt, tie in CASES:
        n, g = astar(raw, W, H, b[0], b[1], a[0], a[1], wgt, tie)
        print("   %-16s expansions=%7d  len=%s" % (label, n, "%.1f" % g if g else "-"))

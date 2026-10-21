"""Batch D probe 14: settle the walkability question with two independent tests.

1. Connectivity using the GAME's movement rule (Game.java:1266-1267: 8-way, but
   a diagonal step needs both orthogonal neighbours free -- no corner cutting).
   _d9.py used strict 4-way, which is stricter than the engine and can split a
   region that a diagonal ramp actually joins.

2. Unit placement as ground truth: every mineral field / geyser the CHK places
   sits on ground a worker must reach, so a correct walk map marks those
   minitiles walkable. Compare interpretations of the VF4 flag word.
"""
import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm

ASSETS = os.path.join(pm.ROOT, r"AndroidPort\app\app\src\main\assets\maps")
DX = (1, 1, 0, -1, -1, -1, 0, 1)
DY = (0, 1, 1, 1, 0, -1, -1, -1)


def load_map(mid):
    d = os.path.join(ASSETS, mid)
    meta = pm.json.load(open(os.path.join(d, "meta.json"), encoding="utf8"))
    walk = open(os.path.join(d, "walk.bin"), "rb").read()
    return d, meta, walk


def regions(walk, W4, H4):
    lab = [-1] * (W4 * H4)
    regs = []
    for i in range(W4 * H4):
        if walk[i] and lab[i] < 0:
            rid = len(regs)
            dq = collections.deque([i])
            lab[i] = rid
            n = 0
            while dq:
                j = dq.popleft()
                n += 1
                x, y = j % W4, j // W4
                for k in range(8):
                    nx, ny = x + DX[k], y + DY[k]
                    if not (0 <= nx < W4 and 0 <= ny < H4):
                        continue
                    o = ny * W4 + nx
                    if not walk[o] or lab[o] >= 0:
                        continue
                    if DX[k] and DY[k]:
                        # no corner cutting, matching Game.java:1266
                        if not walk[y * W4 + nx] or not walk[ny * W4 + x]:
                            continue
                    lab[o] = rid
                    dq.append(o)
            regs.append(n)
    return lab, regs


def nearest(walk, W4, H4, px, py):
    x0, y0 = min(W4 - 1, max(0, px // 8)), min(H4 - 1, max(0, py // 8))
    for r in range(0, 60):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                x, y = x0 + dx, y0 + dy
                if 0 <= x < W4 and 0 <= y < H4 and walk[y * W4 + x]:
                    return x, y
    return None


print("--- connectivity, engine rule (8-way, no corner cutting)")
for mid in sorted(os.listdir(ASSETS)):
    if not os.path.isdir(os.path.join(ASSETS, mid)):
        continue
    d, meta, walk = load_map(mid)
    w, h = meta["w"], meta["h"]
    W4, H4 = w * 4, h * 4
    lab, regs = regions(walk, W4, H4)
    ok = []
    for sx, sy in meta["starts"]:
        p = nearest(walk, W4, H4, sx, sy)
        ok.append(bool(p and lab[p[1] * W4 + p[0]] >= 0))
    seed = nearest(walk, W4, H4, *meta["starts"][0])
    reach = sum(1 for i in range(W4 * H4) if walk[i] and lab[i] == lab[seed[1] * W4 + seed[0]])
    print("   %-12s starts=%-2d connected=%-5s regions=%-3d from-start0=%d/%d=%.1f%%" % (
        mid, len(meta["starts"]), all(ok), len(regs), reach, sum(walk),
        100.0 * reach / max(1, sum(walk))))

print()
print("--- unit placement vs walkability (minerals/geysers must be reachable)")
SRC = {m: s for s, m, _n in pm.MAPS}
for mid in sorted(os.listdir(ASSETS)):
    if not os.path.isdir(os.path.join(ASSETS, mid)):
        continue
    d, meta, walk = load_map(mid)
    w, h = meta["w"], meta["h"]
    W4, H4 = w * 4, h * 4
    bad = []
    for u in meta["units"]:
        p = nearest(walk, W4, H4, u["x"], u["y"])
        if p is None:
            bad.append(u)
    print("   %-12s units=%-3d no-walkable-ground-near=%d" % (
        mid, len(meta["units"]), len(bad)))

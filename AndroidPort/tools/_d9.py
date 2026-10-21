"""Batch D probe 9: after the CV5/VX4 fix the walkability map changed too.
Re-validate that every start location is connected to every other on each map
(the docstring's original acceptance test), and report unreachable pockets.
"""
import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm

ASSETS = os.path.join(pm.ROOT, r"AndroidPort\app\app\src\main\assets\maps")

for mid in sorted(os.listdir(ASSETS)):
    d = os.path.join(ASSETS, mid)
    if not os.path.isdir(d):
        continue
    meta = pm.json.load(open(os.path.join(d, "meta.json"), encoding="utf8"))
    w, h = meta["w"], meta["h"]
    W4, H4 = w * 4, h * 4
    walk = open(os.path.join(d, "walk.bin"), "rb").read()
    starts = meta["starts"]
    if not starts:
        print("   %-12s no starts" % mid)
        continue
    # flood fill from the first start's nearest walkable pixel
    def nearest_walkable(px, py):
        x0, y0 = min(W4 - 1, max(0, px // 8)), min(H4 - 1, max(0, py // 8))
        for r in range(0, 40):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    x, y = x0 + dx, y0 + dy
                    if 0 <= x < W4 and 0 <= y < H4 and walk[y * W4 + x]:
                        return x, y
        return None
    seed = nearest_walkable(starts[0][0], starts[0][1])
    if seed is None:
        print("   %-12s start0 not near walkable ground" % mid)
        continue
    seen = bytearray(W4 * H4)
    dq = collections.deque([seed])
    seen[seed[1] * W4 + seed[0]] = 1
    n = 0
    while dq:
        x, y = dq.popleft()
        n += 1
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W4 and 0 <= ny < H4:
                i = ny * W4 + nx
                if walk[i] and not seen[i]:
                    seen[i] = 1
                    dq.append((nx, ny))
    free = sum(walk)
    ok = []
    for i, (sx, sy) in enumerate(starts):
        p = nearest_walkable(sx, sy)
        ok.append(bool(p and seen[p[1] * W4 + p[0]]))
    print("   %-12s starts=%-2d all-connected=%-5s reachable=%d/%d=%.1f%%" % (
        mid, len(starts), all(ok), n, free, 100.0 * n / max(1, free)))

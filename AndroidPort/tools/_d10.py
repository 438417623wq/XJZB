"""Batch D probe 10: divide is the one map whose starts are not connected.
Dump where each start lands, the size of each connected region, and render the
walkability map to PNG so the shape is visible.
"""
import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from PIL import Image

d = os.path.join(pm.ROOT, r"AndroidPort\app\app\src\main\assets\maps\divide")
meta = pm.json.load(open(os.path.join(d, "meta.json"), encoding="utf8"))
w, h = meta["w"], meta["h"]
W4, H4 = w * 4, h * 4
walk = open(os.path.join(d, "walk.bin"), "rb").read()
print("divide %dx%d tiles  %dx%d minitiles  starts=%s" % (w, h, W4, H4, meta["starts"]))

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
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < W4 and 0 <= ny < H4:
                    k = ny * W4 + nx
                    if walk[k] and lab[k] < 0:
                        lab[k] = rid
                        dq.append(k)
        regs.append(n)
print("regions=%d sizes(top8)=%s" % (len(regs), sorted(regs, reverse=True)[:8]))

def nearest(px, py):
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

for i, (sx, sy) in enumerate(meta["starts"]):
    p = nearest(sx, sy)
    print("  start%d at tile(%d,%d) px(%d,%d) -> mini%s region=%s" % (
        i, sx // 32, sy // 32, sx, sy, p, lab[p[1] * W4 + p[0]] if p else None))

# also: how many minitiles does each start's own CV5 megatile mark walkable
T = pm.load_tileset("jungle")
print("jungle vf4_flags[0]=%s" % T["vf4_flags"][0])
print("jungle vx4_refs[0]=%s" % T["vx4_refs"][0])

img = Image.new("RGB", (W4, H4))
px = img.load()
for y in range(H4):
    for x in range(W4):
        i = y * W4 + x
        if not walk[i]:
            px[x, y] = (0, 0, 0)
        else:
            r = lab[i] % 6
            px[x, y] = [(80, 200, 120), (90, 140, 255), (240, 200, 90),
                        (230, 110, 110), (190, 120, 240), (120, 230, 230)][r]
for sx, sy in meta["starts"]:
    mx, my = sx // 8, sy // 8
    for yy in range(-3, 4):
        for xx in range(-3, 4):
            if 0 <= mx + xx < W4 and 0 <= my + yy < H4 and abs(xx) + abs(yy) < 5:
                px[mx + xx, my + yy] = (255, 0, 0)
img.resize((W4 * 3, H4 * 3), Image.NEAREST).save("_d10_divide_walk.png")
print("saved _d10_divide_walk.png")

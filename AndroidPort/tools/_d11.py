"""Batch D probe 11: overlay divide's walkability on its rendered terrain, with
a distinct colour per connected region, so we can tell a genuine river/cliff
divide from a decode error.
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

terr = Image.new("RGB", (w * 32, h * 32))
for f in os.listdir(d):
    if f.startswith("c_") and f.endswith(".png"):
        cx, cy = f[2:-4].split("_")
        terr.paste(Image.open(os.path.join(d, f)), (int(cx) * 512, int(cy) * 512))

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

order = sorted(range(len(regs)), key=lambda r: -regs[r])
COL = [(0, 255, 0), (255, 0, 255), (255, 255, 0), (0, 255, 255),
       (255, 128, 0), (128, 0, 255), (255, 255, 255), (0, 128, 255),
       (255, 0, 0)]
rank = {r: i for i, r in enumerate(order)}
print("regions=%d" % len(regs))
for r in order:
    print("   region %d size %d  colour %s" % (r, regs[r], COL[rank[r] % len(COL)]))

ov = terr.copy()
px = ov.load()
for y in range(H4):
    for x in range(W4):
        i = y * W4 + x
        if not walk[i]:
            continue
        c = COL[rank[lab[i]] % len(COL)]
        for yy in range(8):
            for xx in range(8):
                X, Y = x * 8 + xx, y * 8 + yy
                if X < ov.width and Y < ov.height:
                    px[X, Y] = tuple((px[X, Y][k] * 3 + c[k]) // 4 for k in range(3))
for sx, sy in meta["starts"]:
    for yy in range(-16, 17):
        for xx in range(-16, 17):
            if abs(xx) < 4 or abs(yy) < 4:
                X, Y = sx + xx, sy + yy
                if 0 <= X < ov.width and 0 <= Y < ov.height:
                    px[X, Y] = (255, 0, 0)
ov.save("_d11_divide_overlay.png")
print("saved _d11_divide_overlay.png  %dx%d" % ov.size)

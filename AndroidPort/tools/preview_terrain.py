"""Preview the terrain the Android game generates (mirrors Game.java exactly)."""

import random
from PIL import Image

W = H = 64
rnd = random.Random(1234)

n = [[0.0] * H for _ in range(W)]
for oct_ in range(5):
    step = 1 << (5 - oct_)
    gw, gh = W // step + 2, H // step + 2
    grid = [[rnd.random() for _ in range(gh)] for _ in range(gw)]
    amp = 1.0 / (oct_ + 1)
    for x in range(W):
        for y in range(H):
            gx, gy = x // step, y // step
            fx = (x % step) / step
            fy = (y % step) / step
            fx = fx * fx * (3 - 2 * fx)
            fy = fy * fy * (3 - 2 * fy)
            top = grid[gx][gy] + (grid[gx + 1][gy] - grid[gx][gy]) * fx
            bot = grid[gx][gy + 1] + (grid[gx + 1][gy + 1] - grid[gx][gy + 1]) * fx
            n[x][y] += (top + (bot - top) * fy) * amp

vals = [n[x][y] for x in range(W) for y in range(H)]
lo, hi = min(vals), max(vals)
span = max(1e-6, hi - lo)

tiles = [[0] * H for _ in range(W)]
walk = [[1] * H for _ in range(W)]
for x in range(W):
    for y in range(H):
        v = (n[x][y] - lo) / span
        if v < 0.26:
            tiles[x][y], walk[x][y] = 0, 0
        elif v < 0.36:
            tiles[x][y] = 1
        elif v < 0.74:
            tiles[x][y] = 2
        else:
            tiles[x][y] = 3

for _ in range(W * H // 110):
    x = 8 + rnd.randrange(max(1, W - 16))
    y = 8 + rnd.randrange(max(1, H - 16))
    walk[x][y] = 0
    tiles[x][y] = 4


def clear(cx, cy, r):
    for x in range(cx - r, cx + r + 1):
        for y in range(cy - r, cy + r + 1):
            if 0 <= x < W and 0 <= y < H and ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 <= r:
                walk[x][y] = 1
                if tiles[x][y] == 0:
                    tiles[x][y] = 2


clear(6, 6, 8)
clear(W - 8, H - 8, 8)

COL = {0: (24, 60, 130), 1: (150, 132, 88), 2: (46, 104, 52),
       3: (96, 90, 84), 4: (58, 54, 50)}
img = Image.new("RGB", (W, H))
px = img.load()
for x in range(W):
    for y in range(H):
        v = ((x * 31 + y * 17) % 5) * 4 - 8
        r, g, b = COL[tiles[x][y]]
        px[x, y] = (max(0, min(255, r + v)), max(0, min(255, g + v)), max(0, min(255, b + v)))

# mark the two spawn clearings
for (cx, cy, col) in ((6, 6, (80, 170, 255)), (W - 8, H - 8, (255, 90, 80))):
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            if 0 <= cx + dx < W and 0 <= cy + dy < H:
                px[cx + dx, cy + dy] = col

img.resize((W * 8, H * 8), Image.NEAREST).save(
    r"F:\KF\XJZB\AndroidPort\extracted\terrain_preview.png")

blocked = sum(1 for x in range(W) for y in range(H) if not walk[x][y])
print("wrote terrain_preview.png   impassable tiles = %d/%d" % (blocked, W * H))

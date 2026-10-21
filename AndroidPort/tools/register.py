from PIL import Image
import statistics

base = r'F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide'
world = Image.new('RGB', (2048, 2048))
for cy in range(4):
    for cx in range(4):
        im = Image.open(base + '\c_%d_%d.webp' % (cx, cy)).convert('RGB')
        world.paste(im, (cx * 512, cy * 512))
wp = world.load()

im1 = Image.open(r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\ceb98bc41cacc4d5590282f1cebdd421.jpg').convert('RGB')
sp = im1.load()

def score(camX, camY, z, px0, py0, pw, ph, step=4):
    """mean abs diff of screenshot rect vs world canvas"""
    tot = 0; n = 0
    for y in range(py0, py0 + ph, step):
        wy = camY + (y - 600) / z
        for x in range(px0, px0 + pw, step):
            wx = camX + (x - 1304) / z
            wxi, wyi = int(wx), int(wy)
            if not (0 <= wxi < 2048 and 0 <= wyi < 2048): return 1e9
            a = sp[x, y]; b = wp[wxi, wyi]
            tot += abs(a[0]-b[0]) + abs(a[1]-b[1]) + abs(a[2]-b[2]); n += 1
    return tot / n

# search around camX=1024, camY=626, z=1.335 with two patches (avoiding bands/HUD)
patches = [(560, 300, 200, 90), (1450, 950, 200, 110), (1900, 200, 200, 120)]
best = None
z = 1.335
for camY in range(590, 665, 2):
    for camX in range(990, 1060, 2):
        s = sum(score(camX, camY, z, *p) for p in patches)
        if best is None or s < best[0]:
            best = (s, camX, camY)
print('best coarse:', best)
_, bx, by = best
best2 = None
for zc in (1.31, 1.32, 1.33, 1.335, 1.34, 1.35, 1.36):
    for dx in range(-6, 7, 2):
        for dy in range(-6, 7, 2):
            s = sum(score(bx+dx, by+dy, zc, *p) for p in patches)
            if best2 is None or s < best2[0]:
                best2 = (s, bx+dx, by+dy, zc)
print('best fine:', best2)
s, camX, camY, z = best2
print()
print('FINAL: camX=%d camY=%d zoom=%.3f  (score %.1f)' % (camX, camY, z, s))
for name, sy0, sy1 in [('strip1-left', 412, 427), ('strip1-right', 435, 450),
                       ('strip2-left', 1102, 1130), ('strip2-right', 1130, 1155),
                       ('blob', 701, 741)]:
    wy0 = camY + (sy0 - 600) / z; wy1 = camY + (sy1 - 600) / z
    print('%-14s screen y %d-%d -> world y %.1f..%.1f  (tile row %.2f..%.2f, chunk boundary offset %+.1f)'
          % (name, sy0, sy1, wy0, wy1, wy0/32, wy1/32, min(abs(wy0-512), abs(wy0-1024))))

"""Decisive test: what does the ART look like at divide's 7 blocking minitiles?

If the art there is a ramp/slope, the walk bitmap is a bake defect (the repack's
VF4 data lost the ramp). If it is solid cliff rock, the map really is divided.
"""
import gzip, os
from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
CELLS = [(189, 14), (109, 131), (110, 130), (111, 129), (158, 106), (159, 107), (216, 164)]

# stitch the 4x4 chunk grid into one world image
world = Image.new("RGB", (2048, 2048))
for cy in range(4):
    for cx in range(4):
        p = os.path.join(ASSETS, "c_%d_%d.webp" % (cx, cy))
        world.paste(Image.open(p).convert("RGB"), (cx * 512, cy * 512))

# one big sheet: 7 crops of 8x8 minitiles (=64x64 world px) upscaled x8
S = 8          # minitiles per side to crop
UP = 8         # upscale
tile = S * 8 * UP
sheet = Image.new("RGB", (tile * 4, tile * 2), (20, 20, 20))
for i, (mx, my) in enumerate(CELLS):
    x0, y0 = mx * 8 - (S // 2) * 8, my * 8 - (S // 2) * 8
    crop = world.crop((x0, y0, x0 + S * 8, y0 + S * 8)).resize((tile, tile), Image.NEAREST)
    px = crop.load()
    # outline the centre minitile (the blocked one) in red
    c0 = (S // 2) * 8 * UP
    for d in range(UP):
        for k in range(8 * UP):
            px[c0 + k, c0 + d] = (255, 0, 0)
            px[c0 + k, c0 + 8 * UP - 1 - d] = (255, 0, 0)
            px[c0 + d, c0 + k] = (255, 0, 0)
            px[c0 + 8 * UP - 1 - d, c0 + k] = (255, 0, 0)
    sheet.paste(crop, ((i % 4) * tile, (i // 4) * tile))
    print("cell %2d minitile(%3d,%3d) worldpx=(%4d,%4d)" % (i, mx, my, mx * 8, my * 8))
sheet.save(os.path.join(OUT, "_divide_cellart.png"))
print("wrote", os.path.join(OUT, "_divide_cellart.png"))

# also: classify each cell's art as water / rock / grass by average colour
for mx, my in CELLS:
    box = world.crop((mx * 8, my * 8, mx * 8 + 8, my * 8 + 8))
    px = list(box.getdata())
    r = sum(p[0] for p in px) / len(px)
    g = sum(p[1] for p in px) / len(px)
    b = sum(p[2] for p in px) / len(px)
    kind = "water" if b > r + 20 else ("rock" if abs(r - g) < 26 and r > 70 else "grass/other")
    print("  minitile(%3d,%3d) avg=(%5.1f,%5.1f,%5.1f) -> %s" % (mx, my, r, g, b, kind))

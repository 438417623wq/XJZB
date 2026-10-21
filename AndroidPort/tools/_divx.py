"""v2.44: is there a crossing between divide's two landmasses?

(2)The Small Divide is a Blizzard ladder map, and a ladder map has to be
playable -- so the walk bitmap claiming the two bases are unreachable is
suspicious. This renders the region around the cheapest crossing at high zoom,
from the baked art, so a bridge or ramp would be visible, and marks the blocked
minitiles.
"""
import gzip
import os

from PIL import Image, ImageDraw

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
MAP = os.path.join(ASSETS, "maps", "divide")

with open(os.path.join(MAP, "meta.txt"), "r", encoding="utf-8", errors="replace") as f:
    meta = f.read()
W = H = 0
for line in meta.splitlines():
    if line.startswith("w="):
        W = int(line[2:])
    elif line.startswith("h="):
        H = int(line[2:])

with gzip.open(os.path.join(MAP, "walk.bin.gz"), "rb") as f:
    raw = f.read()
MW, MH = W * 4, H * 4
walk = [b != 0 for b in raw]

# Stitch the 4x4 chunk grid into the full 2048x2048 world image.
world = Image.new("RGB", (W * 32, H * 32), (0, 0, 0))
for cy in range(H // 16):
    for cx in range(W // 16):
        p = os.path.join(MAP, "c_%d_%d.webp" % (cx, cy))
        if not os.path.exists(p):
            continue
        world.paste(Image.open(p).convert("RGB"), (cx * 512, cy * 512))
print("world %s" % (world.size,))

BLOCKED = [
    (189, 14), (109, 131), (110, 130), (111, 129), (158, 106), (159, 107), (216, 164),
]

# One panel per blocked cell: 24x24 minitiles = 192x192 world px at 4x.
TILE = 4
CELLS = 24
for i, (mx, my) in enumerate(BLOCKED):
    wx, wy = mx * 8, my * 8
    box = (wx - CELLS * TILE, wy - CELLS * TILE, wx + CELLS * TILE, wy + CELLS * TILE)
    crop = world.crop(box).resize((CELLS * TILE * 2, CELLS * TILE * 2), Image.NEAREST)
    crop = Image.eval(crop, lambda v: min(255, int(v * 1.9)))
    d = ImageDraw.Draw(crop)
    # red outline on every non-walkable minitile, green on walkable
    for yy in range(CELLS * 2):
        for xx in range(CELLS * 2):
            gx = (box[0] // 8) + xx
            gy = (box[1] // 8) + yy
            ok = 0 <= gx < MW and 0 <= gy < MH and walk[gy * MW + gx]
            col = (0, 255, 0) if ok else (255, 0, 0)
            px, py = xx * 8, yy * 8
            d.rectangle([px, py, px + 7, py + 7], outline=col)
    # centre cell heavy
    cx = CELLS * 2
    d.rectangle([cx * 8, cx * 8, cx * 8 + 7, cx * 8 + 7], outline=(255, 255, 0), width=2)
    crop.save(os.path.join(OUT, "_divx_%d_%d_%d.png" % (i, mx, my)))
    print("  cell %d minitile(%d,%d) worldpx(%d,%d) -> _divx_%d_%d_%d.png" % (i, mx, my, wx, wy, i, mx, my))

# Also a wide view of the whole diagonal divide band, with blocked cells in red.
wide = world.copy()
d = ImageDraw.Draw(wide)
for my in range(MH):
    for mx in range(MW):
        if not walk[my * MW + mx]:
            d.rectangle([mx * 8, my * 8, mx * 8 + 7, my * 8 + 7], fill=(255, 0, 0))
wide = Image.eval(wide, lambda v: min(255, int(v * 1.2)))
wide = wide.resize((1024, 1024), Image.NEAREST)
wide.save(os.path.join(OUT, "_divx_wide.png"))
print("wide -> _divx_wide.png")

# minimap for reference
mp = os.path.join(MAP, "minimap.webp")
if os.path.exists(mp):
    m = Image.open(mp).convert("RGB").resize((512, 512), Image.NEAREST)
    m.save(os.path.join(OUT, "_divx_minimap.png"))
    print("minimap %s -> _divx_minimap.png" % (Image.open(mp).size,))

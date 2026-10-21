"""v2.10: verify the generated protoss sheets the way the game will read them.

This does not re-read the GRPs -- it reads the finished
assets/sprites/<key>_b.png and slices them exactly as SpriteBank/GameView do
(17 direction columns, row 0..walkCount-1 = walk, row walkCount = attack), so a
mistake in the walk/attack row arithmetic shows up here rather than on a phone.

For every protoss unit it prints the manifest row and dumps one strip per
animation row at direction 8.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw

ROOT = r"F:\KF\XJZB"
SPR = os.path.join(ROOT, r"AndroidPort\app\app\src\main\assets\sprites")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "v210_sheet")
os.makedirs(OUT, exist_ok=True)

PROTOSS = ["probe", "zealot", "dragoon", "templar", "dtemplar", "archon",
           "darchon", "shuttle", "scout", "corsair", "arbiter", "carrier",
           "intercep", "reaver", "observer"]

manifest = {}
with open(os.path.join(SPR, "manifest.txt"), encoding="utf8") as fp:
    for line in fp:
        p = line.strip().split(",")
        if len(p) >= 6:
            manifest[p[0]] = p

for key in PROTOSS:
    row = manifest.get(key)
    if row is None:
        print("MISSING manifest", key)
        continue
    kind, walk, atk, frames, cols = (int(row[1]), int(row[2]), int(row[3]),
                                     int(row[4]), int(row[5]))
    p = os.path.join(SPR, "%s_b.png" % key)
    im = Image.open(p).convert("RGBA")
    rows = max(1, walk + atk)
    fw, fh = im.width // 17, im.height // rows
    print("%-9s kind=%d walk=%d atk=%d rows=%d cell=%dx%d sheet=%dx%d"
          % (key, kind, walk, atk, rows, fw, fh, im.width, im.height))

    Z = max(1, min(3, 900 // max(fw * rows, 1)))
    strip = Image.new("RGBA", (im.width * Z, (fh * Z + 16) * rows), (22, 22, 30, 255))
    d = ImageDraw.Draw(strip)
    for r in range(rows):
        cell = im.crop((8 * fw, r * fh, 9 * fw, (r + 1) * fh))
        cell = cell.resize((fw * Z, fh * Z), Image.NEAREST)
        strip.paste(cell, (8 * fw * Z, r * (fh * Z + 16)), cell)
        # also show direction 4 so a wrong direction stride is visible
        cell4 = im.crop((4 * fw, r * fh, 5 * fw, (r + 1) * fh))
        cell4 = cell4.resize((fw * Z, fh * Z), Image.NEAREST)
        strip.paste(cell4, (4 * fw * Z, r * (fh * Z + 16)), cell4)
        tag = "walk%d" % r if r < walk else "ATTACK"
        d.text((4, r * (fh * Z + 16) + fh * Z + 2), tag, fill=(255, 255, 0, 255))
    strip.save(os.path.join(OUT, "%s.png" % key))

print("wrote", OUT)

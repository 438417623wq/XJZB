"""Batch E probe 2b: slice icons.pcx into its tile grid and label it."""
import os, sys, struct
sys.path.insert(0, ".")
import sc_archive
from PIL import Image, ImageDraw

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
p = "glue\\Battle.net\\icons\\icons.pcx"
for ar in (SD, BD):
    if ar.has(p):
        d, gaps = ar.read_with_gaps(p)
        break
w = h = 112
pal = d[-768:]
px = bytearray()
i = 128
while len(px) < w * h and i < len(d) - 768:
    b = d[i]; i += 1
    if b & 0xC0 == 0xC0:
        cnt = b & 0x3F
        px.extend(bytes([d[i]]) * cnt); i += 1
    else:
        px.append(b)
if len(px) < w * h:
    px.extend(bytes(w * h - len(px)))
lut = [(pal[k * 3], pal[k * 3 + 1], pal[k * 3 + 2]) for k in range(256)]

# find the tile pitch: 112 = 7*16 = 8*14 = 14*8 = 16*7
for pitch in (16, 14, 8, 28, 56):
    print("pitch %d -> %d x %d tiles" % (pitch, w // pitch, h // pitch))

P = 16
Z = 6
sheet = Image.new("RGB", ((w // P) * P * Z + 20, (h // P) * P * Z + 20), (20, 20, 26))
dr = ImageDraw.Draw(sheet)
for ty in range(h // P):
    for tx in range(w // P):
        tile = Image.new("RGB", (P, P))
        data = []
        for y in range(P):
            for x in range(P):
                data.append(lut[px[(ty * P + y) * w + (tx * P + x)]])
        tile.putdata(data)
        tile = tile.resize((P * Z, P * Z), Image.NEAREST)
        ox, oy = tx * P * Z + 10, ty * P * Z + 10
        sheet.paste(tile, (ox, oy))
        dr.text((ox + 2, oy + 2), "%d,%d" % (tx, ty), fill=(255, 255, 0))
        dr.rectangle([ox - 1, oy - 1, ox + P * Z, oy + P * Z], outline=(80, 90, 110))
sheet.save(os.path.join(OUT, "_e2_tiles.png"))
print("wrote _e2_tiles.png", sheet.size)

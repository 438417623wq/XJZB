"""Batch E probe 2c: render icons.pcx at several tile pitches to find the grid."""
import os, sys
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

base = Image.new("RGB", (w, h))
base.putdata([lut[v] for v in px[:w * h]])

for P in (28, 32, 56):
    cols = w // P
    rows = h // P
    if cols == 0 or rows == 0:
        continue
    Z = 5
    sheet = Image.new("RGB", (cols * P * Z + 20, rows * P * Z + 20), (20, 20, 26))
    dr = ImageDraw.Draw(sheet)
    for ty in range(rows):
        for tx in range(cols):
            tile = base.crop((tx * P, ty * P, tx * P + P, ty * P + P))
            tile = tile.resize((P * Z, P * Z), Image.NEAREST)
            ox, oy = tx * P * Z + 10, ty * P * Z + 10
            sheet.paste(tile, (ox, oy))
            dr.text((ox + 3, oy + 3), "%d,%d" % (tx, ty), fill=(255, 255, 0))
            dr.rectangle([ox - 1, oy - 1, ox + P * Z, oy + P * Z], outline=(90, 100, 120))
    fn = os.path.join(OUT, "_e2_p%d.png" % P)
    sheet.save(fn)
    print("pitch %d -> %dx%d tiles -> %s %s" % (P, cols, rows, fn, sheet.size))

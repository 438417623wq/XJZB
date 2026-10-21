"""Batch E probe 2: decode glue\\Battle.net\\icons\\icons.pcx and dump it."""
import os, sys, struct
sys.path.insert(0, ".")
import sc_archive
from PIL import Image

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out")
os.makedirs(OUT, exist_ok=True)
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

p = "glue\\Battle.net\\icons\\icons.pcx"
for ar in (SD, BD):
    if ar.has(p):
        d, gaps = ar.read_with_gaps(p)
        break

print("file bytes", len(d), "gaps", gaps)
print("head 16:", d[:16].hex(" "))
print("hdr: manuf=%d ver=%d enc=%d bpp=%d" % (d[0], d[1], d[2], d[3]))
xmin, ymin, xmax, ymax = struct.unpack_from("<HHHH", d, 4)
print("xmin=%d ymin=%d xmax=%d ymax=%d -> %dx%d" % (xmin, ymin, xmax, ymax,
                                                   xmax - xmin + 1, ymax - ymin + 1))
print("hdpi=%d vdpi=%d" % struct.unpack_from("<HH", d, 12))
print("nplanes=%d bpl=%d palette_info=%d" % (d[65], struct.unpack_from("<H", d, 66)[0], struct.unpack_from("<H", d, 68)[0]))
print("tail 769 first byte (palette marker) = 0x%02x" % d[-769])
pal = d[-768:]
print("palette first 8:", [tuple(pal[i*3:i*3+3]) for i in range(8)])

w = xmax - xmin + 1
h = ymax - ymin + 1
px = bytearray()
i = 128
while len(px) < w * h and i < len(d) - 768:
    b = d[i]
    i += 1
    if b & 0xC0 == 0xC0:
        cnt = b & 0x3F
        if i >= len(d) - 768:
            break
        px.extend(bytes([d[i]]) * cnt)
        i += 1
    else:
        px.append(b)
print("decoded %d of %d pixels (consumed %d of %d bytes)" % (len(px), w * h, i, len(d) - 768))
if len(px) < w * h:
    px.extend(bytes(w * h - len(px)))

lut = [(pal[k * 3], pal[k * 3 + 1], pal[k * 3 + 2]) for k in range(256)]
img = Image.new("RGB", (w, h))
img.putdata([lut[v] for v in px[:w * h]])
img = img.resize((w * 4, h * 4), Image.NEAREST)
img.save(os.path.join(OUT, "_e2_icons.png"))
print("wrote _e2_icons.png", img.size)

# colour histogram: which palette entries are used, to locate icon blocks
from collections import Counter
cnt = Counter(px[:w * h])
print("distinct colours used:", len(cnt))
print("top 12:", cnt.most_common(12))

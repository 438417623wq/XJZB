"""Decisive palette-order test on tileset-INDEPENDENT art.

min01 (mineral), wireframe portraits, and the muzzle flash are drawn from the
same WPE palette but are NOT tileset art, so their canonical StarCraft colours
are fixed facts:
    mineral field   = BLUE crystals
    Terran portrait = blue-grey armour, tan face
    muzzle flash    = ORANGE/white core
Whatever channel order reproduces those is correct.
"""
import os
from PIL import Image, ImageDraw
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
if len(wpe) < 1024:
    wpe += bytes(1024 - len(wpe))
BGR = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]
RGB = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def fimg(f, pal):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    p = im.load()
    for y in range(f["h"]):
        for x in range(f["w"]):
            o = y * f["w"] + x
            if o < len(f["px"]) and f["px"][o] != 255:
                p[x, y] = pal[f["px"][o]] + (255,)
    return im


wire = load(r"unit\wirefram\wirefram.grp")     # 228 portraits
mineral = load(r"unit\neutral\min01.grp")
marine = load(r"unit\terran\marine.grp")
bang = load(r"unit\thingy\tBangL.grp")

ITEMS = [
    ("min01 BLUE?", mineral[0][0]),
    ("wire[0] marine", wire[0][0]),
    ("wire[7] scv", wire[0][7]),
    ("wire[106] cc", wire[0][106]),
    ("marine f0", marine[0][0]),
    ("bangL mid ORANGE?", bang[0][len(bang[0]) // 2]),
]

sc = 5
rows = [("BGR (shipped pipeline)", BGR), ("RGB (raw byte order)", RGB)]
maxh = max(f["h"] for _, f in ITEMS)
W = sum(f["w"] * sc + 10 for _, f in ITEMS) + 12
H = (maxh * sc + 44) * len(rows) + 8
canvas = Image.new("RGB", (max(W, 1200), H), (26, 28, 36))
d = ImageDraw.Draw(canvas)
y = 4
for nm, pal in rows:
    d.text((4, y), nm, fill=(120, 255, 140)); y += 16
    x = 4
    for label, f in ITEMS:
        im = fimg(f, pal)
        big = im.resize((im.width * sc, im.height * sc), Image.NEAREST)
        canvas.paste(big, (x, y), big)
        d.text((x, y + big.height + 2), label, fill=(200, 210, 230))
        x += big.width + 10
    y += maxh * sc + 44
canvas.save(os.path.join(OUT, "palette_decisive.png"))
print("wrote palette_decisive.png", canvas.size)

# numeric: is the mineral blue or brown?
for nm, pal in (("BGR", BGR), ("RGB", RGB)):
    im = fimg(mineral[0][0], pal)
    from collections import Counter
    c = Counter()
    for yy in range(im.height):
        for xx in range(im.width):
            r, g, b, a = im.getpixel((xx, yy))
            if a and r + g + b > 120:
                c[(r, g, b)] += 1
    print("mineral %s top: %s" % (nm, c.most_common(3)))

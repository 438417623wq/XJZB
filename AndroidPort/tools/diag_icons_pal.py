"""Decide the WPE channel order from ICONIC art whose colour is certain.

Ground truth (StarCraft, universally known):
  * move order icon   = green arrow
  * stop order icon   = red octagon
  * attack icon       = red crosshair
  * mineral crystals  = blue/cyan
  * Terran marine     = blue-grey armour, tan face

Renders each under both channel orders; whichever reproduces the canonical
colours is correct.
"""
import os
from collections import Counter
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


def frame_img(f, pal):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    p = im.load()
    for y in range(f["h"]):
        for x in range(f["w"]):
            o = y * f["w"] + x
            if o < len(f["px"]) and f["px"][o] != 255:
                p[x, y] = pal[f["px"][o]] + (255,)
    return im


def dom(im, n=4):
    c = Counter()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if a and (r + g + b) > 90:      # ignore near-black outlines
                c[(r, g, b)] += 1
    return c.most_common(n)


cmd = load(r"unit\cmdbtns\cmdicons.grp")
frames, mw, mh = cmd

ICONS = [("move(green)", 228), ("stop(red)", 229), ("attack(red)", 230),
         ("harvest(blue)", 231), ("scv(yellow)", 7), ("marine", 0),
         ("cc(grey)", 106), ("turret(grey)", 124)]

print("=== iconic icons: dominant colour under each order ===")
for label, idx in ICONS:
    f = frames[idx]
    line = "%-14s " % label
    for nm, pal in (("BGR", BGR), ("RGB", RGB)):
        im = frame_img(f, pal)
        d = dom(im, 2)
        line += " %s=%-28s" % (nm, d)
    print(line)

print("\n=== minerals / geyser ===")
for label, path in [("min01", r"unit\neutral\min01.grp"),
                    ("min02", r"unit\neutral\min02.grp"),
                    ("min03", r"unit\neutral\min03.grp"),
                    ("geyser", r"unit\neutral\Geyser.grp")]:
    r = load(path)
    frames, mw, mh = r
    f = frames[0]
    line = "%-8s " % label
    for nm, pal in (("BGR", BGR), ("RGB", RGB)):
        im = frame_img(f, pal)
        line += " %s=%-26s" % (nm, dom(im, 2))
    print(line)

sc = 4
items = [("move", frames[228]), ("stop", frames[229]), ("attack", frames[230]),
         ("harvest", frames[231]), ("scv", frames[7]), ("marine", frames[0])]
rows = [("BGR (shipped)", BGR), ("RGB (swapped)", RGB)]
W = sum(f["w"] * sc + 8 for _, f in items) + 12
H = sum(mh * sc + 40 for _ in rows) + 8
canvas = Image.new("RGB", (max(W, 900), H), (26, 28, 36))
d = ImageDraw.Draw(canvas)
y = 4
for nm, pal in rows:
    d.text((4, y), nm, fill=(120, 255, 140)); y += 16
    x = 4
    for label, f in items:
        im = frame_img(f, pal)
        big = im.resize((im.width * sc, im.height * sc), Image.NEAREST)
        canvas.paste(big, (x, y), big)
        d.text((x, y + big.height + 2), label, fill=(200, 210, 230))
        x += big.width + 8
    y += mh * sc + 40
canvas.save(os.path.join(OUT, "palette_icons.png"))
print("\nwrote palette_icons.png", canvas.size)

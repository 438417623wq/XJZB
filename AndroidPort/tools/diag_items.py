"""Test byte order with content whose colour is unambiguous.

StarCraft minerals are cyan-blue crystals and vespene geysers are green. Also
renders the marine (blue-grey armour, tan face). Whichever byte order keeps
minerals cyan AND turns explosions orange is the correct one.
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


def frame_img(f, pal):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    p = im.load()
    for y in range(f["h"]):
        for x in range(f["w"]):
            o = y * f["w"] + x
            if o < len(f["px"]) and f["px"][o] != 255:
                p[x, y] = pal[f["px"][o]] + (255,)
    return im


def dominant(im):
    """Most common non-transparent colour, as a sanity label."""
    from collections import Counter
    c = Counter()
    for px in im.getdata():
        if px[3] > 0:
            c[px[:3]] += 1
    return c.most_common(3)


ITEMS = [
    ("mineral", r"unit\neutral\min01.grp"),
    ("geyser", r"unit\neutral\Geyser.grp"),
    ("marine", r"unit\terran\marine.grp"),
    ("bangL", r"unit\thingy\tBangL.grp"),
    ("flshS", r"unit\thingy\tmeFlshS.grp"),
]

sc = 3
rowsH = []
for nm, pal in (("BGR (current)", BGR), ("RGB (swapped)", RGB)):
    imgs = []
    for label, path in ITEMS:
        r = load(path)
        if r is None:
            continue
        frames, mw, mh = r
        f = frames[len(frames) // 2] if label == "bangL" else frames[0]
        if label == "flshS":
            f = max(frames, key=lambda z: sum(1 for v in z["px"] if v != 255))
        im = frame_img(f, pal)
        imgs.append((label, im, dominant(im)))
    rowsH.append((nm, imgs))

W = sum(im.width * sc + 8 for _, im, _ in rowsH[0][1]) + 12
H = sum(max(im.height for _, im, _ in imgs) * sc + 60 for _, imgs in rowsH) + 8
canvas = Image.new("RGB", (max(W, 900), H), (26, 28, 36))
d = ImageDraw.Draw(canvas)
y = 4
for nm, imgs in rowsH:
    d.text((4, y), nm, fill=(120, 255, 140)); y += 16
    x = 4
    for label, im, dom in imgs:
        big = im.resize((im.width * sc, im.height * sc), Image.NEAREST)
        canvas.paste(big, (x, y), big)
        d.text((x, y + big.height + 2), "%s: %s" % (label, dom[0][0]), fill=(200, 210, 230))
        d.text((x, y + big.height + 14), "  %d px" % dom[0][1], fill=(150, 165, 190))
        x += big.width + 8
    y += max(im.height for _, im, _ in imgs) * sc + 60
canvas.save(os.path.join(OUT, "byteorder_items.png"))
print("wrote byteorder_items.png", canvas.size)

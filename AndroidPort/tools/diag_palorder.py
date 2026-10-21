"""Decide the WPE channel order using sprites whose canonical colour is known.

StarCraft colours are unambiguous for these: minerals are cyan-blue crystals,
vespene geysers are green, zerg units are purple/violet, terran structures are
grey-blue, the SCV is yellow-orange. A byte-order swap flips red and blue for
every one of them, so whichever order reproduces the canonical set is correct.
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


def frame_img(f, pal, skip_team):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    p = im.load()
    for y in range(f["h"]):
        for x in range(f["w"]):
            o = y * f["w"] + x
            if o < len(f["px"]) and f["px"][o] != 255:
                v = f["px"][o]
                if skip_team and 8 <= v <= 15:
                    continue          # ignore the recoloured team range
                p[x, y] = pal[v] + (255,)
    return im


def dom(im, top=3):
    c = Counter()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            if a:
                c[(r, g, b)] += 1
    return c.most_common(top)


ITEMS = [
    ("mineral (want cyan/blue)", r"unit\neutral\min01.grp"),
    ("geyser  (want green)", r"unit\neutral\Geyser.grp"),
    ("zergling(want purple)", r"unit\zerg\zergling.grp"),
    ("hydralisk(want purple)", r"unit\zerg\hydra.grp"),
    ("scv     (want yellow)", r"unit\terran\SCV.grp"),
    ("cc      (want grey)", r"unit\terran\control.grp"),
    ("flshS   (want orange)", r"unit\thingy\tmeFlshS.grp"),
    ("bangL   (want orange)", r"unit\thingy\tBangL.grp"),
]

print("=== dominant colours (team range 8-15 ignored) ===")
for label, path in ITEMS:
    r = load(path)
    if r is None:
        print(label, "MISS"); continue
    frames, mw, mh = r
    f = frames[len(frames) // 2]
    line = "%-26s " % label
    for nm, pal in (("BGR", BGR), ("RGB", RGB)):
        im = frame_img(f, pal, True)
        d = dom(im, 2)
        line += "  %s: %s" % (nm, [c for c, n in d])
    print(line)

# visual sheet
sc = 3
rows = []
for nm, pal in (("BGR (current)", BGR), ("RGB (swapped)", RGB)):
    imgs = []
    for label, path in ITEMS:
        r = load(path)
        if r is None:
            continue
        frames, mw, mh = r
        f = frames[len(frames) // 2]
        imgs.append((label.split()[0], frame_img(f, pal, True)))
    rows.append((nm, imgs))

W = sum(im.width * sc + 8 for _, im in rows[0][1]) + 12
H = sum(max(im.height for _, im in imgs) * sc + 40 for _, imgs in rows) + 8
canvas = Image.new("RGB", (max(W, 1200), H), (26, 28, 36))
d = ImageDraw.Draw(canvas)
y = 4
for nm, imgs in rows:
    d.text((4, y), nm, fill=(120, 255, 140)); y += 16
    x = 4
    for label, im in imgs:
        big = im.resize((im.width * sc, im.height * sc), Image.NEAREST)
        canvas.paste(big, (x, y), big)
        d.text((x, y + big.height + 2), label, fill=(200, 210, 230))
        x += big.width + 8
    y += max(im.height for _, im in imgs) * sc + 40
canvas.save(os.path.join(OUT, "palette_order_units.png"))
print("wrote palette_order_units.png", canvas.size)

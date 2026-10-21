"""v2.11: independent check of the zerg building alignment.

The alignment in probe_v211am says unit\\zerg\\Lurker.grp is the SUNKEN COLONY
(not the lurker unit -- the lurker unit is lurknorm.grp). A sunken colony has a
long tentacle attack, a spore colony does not, so if block 1 of Lurker.grp
shows a tentacle the alignment is independently confirmed.

Also renders Snakey.grp vs chrysal.grp next to the Hydralisk Den (135) and
Spawning Pool (142) command icons, because those two are the pair where the
structural argument and a first glance at the art disagree.

Usage: python probe_v211ao.py
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "v211_bld")
os.makedirs(OUT, exist_ok=True)

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def frame_image(f, pal=PAL):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        base = y * f["w"]
        for x in range(f["w"]):
            v = src[base + x]
            if v != 255:
                px[x, y] = pal[v] + (255,)
    return im


def tight(im):
    bb = im.getbbox()
    return im.crop(bb) if bb else im


# ---- part 1: the sunken colony tentacle test -------------------------------
r = load("unit\\zerg\\Lurker.grp")
frames, mw, mh = r
S = 3
cells = []
for d in range(0, 34, 2):
    cells.append(("f%d" % d, tight(frame_image(frames[d]))))
cw = max(c[1].width for c in cells) * S + 8
ch = max(c[1].height for c in cells) * S + 18
cols = 6
rows = (len(cells) + cols - 1) // cols
img = Image.new("RGBA", (cols * cw, rows * ch), (16, 16, 22, 255))
dr = ImageDraw.Draw(img)
for k, (lab, im) in enumerate(cells):
    im = im.resize((im.width * S, im.height * S), Image.NEAREST)
    ox = (k % cols) * cw
    oy = (k // cols) * ch
    dr.text((ox + 4, oy + 3), lab, fill=(140, 255, 170, 255))
    img.paste(im, (ox + 4, oy + 17), im)
p = os.path.join(OUT, "sunken_tentacle.png")
img.save(p)
print("Lurker.grp frames=%d blocks=%d -> %s" % (len(frames), (len(frames) + 16) // 17, p))

# ---- part 2: Snakey vs chrysal vs the two icons ----------------------------
r = load("unit\\cmdbtns\\cmdicons.grp")
icons, imw, imh = r
pairs = [
    ("ICON 135 HydraliskDen", icons[135]),
    ("ICON 142 SpawningPool", icons[142]),
    ("Snakey.grp f0", load("unit\\zerg\\Snakey.grp")[0][0]),
    ("Snakey.grp f2", load("unit\\zerg\\Snakey.grp")[0][2]),
    ("chrysal.grp f0", load("unit\\zerg\\chrysal.grp")[0][0]),
    ("chrysal.grp f3", load("unit\\zerg\\chrysal.grp")[0][3]),
]
S = 5
cw = 260
ch = 260
img = Image.new("RGBA", (3 * cw, 2 * ch), (255, 255, 255, 255))
dr = ImageDraw.Draw(img)
for k, (lab, f) in enumerate(pairs):
    im = tight(frame_image(f))
    sc = min((cw - 20) / max(1, im.width), (ch - 34) / max(1, im.height))
    im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.NEAREST)
    ox = (k % 3) * cw
    oy = (k // 3) * ch
    dr.text((ox + 6, oy + 4), lab, fill=(0, 0, 0, 255))
    img.paste(im, (ox + (cw - im.width) // 2, oy + 30 + (ch - 30 - im.height) // 2), im)
p = os.path.join(OUT, "pool_vs_den.png")
img.save(p)
print("->", p)

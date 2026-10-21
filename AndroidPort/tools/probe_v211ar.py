"""v2.11: compact one-frame-per-block overview for the batch B unit GRPs.

Rendering all 12 full 17-column sheets costs a lot of attention; this shows
ONLY direction 0 of each block, so a whole unit's block structure fits in one
short strip and the walk / attack / death seams are readable at a glance.

Usage: python probe_v211ar.py [scale]
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
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "v211_unit")
os.makedirs(OUT, exist_ok=True)

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

PATHS = [
    # ---- calibration: these four layouts are ALREADY VERIFIED in the shipped
    # manifest, so whatever pattern their blocks show is what "walk" looks like.
    #   marine walk=b0..b2 atk=b3, death at b13
    #   zergling walk=b0..b2 atk=b3, death at b17
    #   hydra walk=b0..b1 atk=b2, death at b17
    #   zealot walk=b0..b4 atk=b5, death at b13
    #   dragoon walk=b0..b7 atk=b8, death at b24
    ("marine", "unit\\terran\\marine.grp"),
    ("zergling", "unit\\zerg\\zergling.grp"),
    ("hydra", "unit\\zerg\\hydra.grp"),
    ("zealot", "unit\\protoss\\zealot.grp"),
    ("dragoon", "unit\\protoss\\dragoon.grp"),
    ("---", None),
    ("ultra", "unit\\zerg\\ultra.grp"),
    ("queen", "unit\\zerg\\queen.grp"),
    ("defiler", "unit\\zerg\\defiler.grp"),
    ("guardian", "unit\\zerg\\guardian.grp"),
    ("devourer", "unit\\zerg\\devour.grp"),
    ("lurker", "unit\\zerg\\lurknorm.grp"),
    ("lurker_bur", "unit\\zerg\\lurkburr.grp"),
    ("broodling", "unit\\zerg\\brood.grp"),
    ("lurk_egg", "unit\\zerg\\LurkEgg.grp"),
    ("medic", "unit\\terran\\medic.grp"),
    ("valkyrie", "unit\\terran\\bomber.grp"),
    ("spider", "unit\\terran\\Spider.grp"),
]

SCALE = int(sys.argv[1]) if len(sys.argv) > 1 else 2
CELL = 150


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def frame_image(f):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        base = y * f["w"]
        for x in range(f["w"]):
            v = src[base + x]
            if v != 255:
                px[x, y] = PAL[v] + (255,)
    return im


def tight(im):
    bb = im.getbbox()
    return im.crop(bb) if bb else im


nb_max = 0
data = []
for key, path in PATHS:
    if path is None:
        data.append((key, None, None, 0))
        continue
    r = load(path)
    if r is None:
        print("MISS", key)
        continue
    frames, mw, mh = r
    nb = (len(frames) + 16) // 17
    nb_max = max(nb_max, nb)
    data.append((key, path, frames, nb))
    print("%-12s frames=%-4d blocks=%-3d" % (key, len(frames), nb))

W = 90 + nb_max * CELL
H = len(data) * CELL
img = Image.new("RGBA", (W, H), (16, 16, 22, 255))
dr = ImageDraw.Draw(img)
for row, (key, path, frames, nb) in enumerate(data):
    y0 = row * CELL
    dr.text((4, y0 + 4), key, fill=(255, 235, 140, 255))
    if frames is None:
        continue
    for b in range(nb):
        fi = b * 17
        if fi >= len(frames):
            break
        im = tight(frame_image(frames[fi]))
        sc = min((CELL - 20) / max(1, im.width), (CELL - 20) / max(1, im.height))
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))),
                       Image.NEAREST)
        ox = 90 + b * CELL
        img.paste(im, (ox + (CELL - im.width) // 2,
                       y0 + 14 + (CELL - 14 - im.height) // 2), im)
        dr.text((ox + 3, y0 + 3), "b%d" % b, fill=(140, 220, 255, 255))

p = os.path.join(OUT, "overview.png")
img.save(p)
print("->", p)

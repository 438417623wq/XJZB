"""v2.11: compact walk/attack reading sheet -- blocks 0..7 only, one row per
unit, sized so the viewer does not downscale it.

The five manifest-verified units come first with their answer in the label; the
remaining batch B units follow. Reading rule (calibrated on those five):
the walk cycle is the run of locomotion poses at the start; the attack is the
first block that clearly adds a weapon flash / strike; a block whose frame count
is < 17 is the death (printed in orange).

Usage: python probe_v211bf.py <part>   part 1 = all, 2 = zerg only
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

ROWS = [
    ("marine  W=3 atk3", "unit\\terran\\marine.grp"),
    ("zergling W=3 atk3", "unit\\zerg\\zergling.grp"),
    ("hydra   W=2 atk2", "unit\\zerg\\hydra.grp"),
    ("zealot  W=5 atk5", "unit\\protoss\\zealot.grp"),
    ("dragoon W=8 atk8", "unit\\protoss\\dragoon.grp"),
    ("---", None),
    ("ultra", "unit\\zerg\\ultra.grp"),
    ("queen", "unit\\zerg\\queen.grp"),
    ("defiler", "unit\\zerg\\defiler.grp"),
    ("guardian", "unit\\zerg\\guardian.grp"),
    ("devourer", "unit\\zerg\\devour.grp"),
    ("lurker", "unit\\zerg\\lurknorm.grp"),
    ("lurker_bur", "unit\\zerg\\lurkburr.grp"),
    ("broodling", "unit\\zerg\\brood.grp"),
    ("medic", "unit\\terran\\medic.grp"),
    ("valkyrie", "unit\\terran\\bomber.grp"),
    ("spider", "unit\\terran\\Spider.grp"),
]

CELL = int(os.environ.get("CELL", "200"))
NCELL = 8
LABW = 230


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


img = Image.new("RGBA", (LABW + NCELL * CELL, len(ROWS) * CELL),
                (16, 16, 22, 255))
dr = ImageDraw.Draw(img)
for r, (lab, path) in enumerate(ROWS):
    y0 = r * CELL
    dr.text((5, y0 + 6), lab, fill=(255, 235, 140, 255))
    if path is None:
        continue
    res = load(path)
    if res is None:
        dr.text((5, y0 + 26), "MISS", fill=(255, 90, 90, 255))
        continue
    frames, mw, mh = res
    nb = (len(frames) + 16) // 17
    dr.text((5, y0 + CELL - 18), "blocks=%d" % nb, fill=(150, 200, 255, 255))
    for b in range(min(nb, NCELL)):
        nfr = min(17, len(frames) - b * 17)
        im = tight(frame_image(frames[b * 17]))
        sc = min((CELL - 22) / max(1, im.width), (CELL - 22) / max(1, im.height))
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))),
                       Image.NEAREST)
        ox = LABW + b * CELL
        img.paste(im, (ox + (CELL - im.width) // 2,
                       y0 + 18 + (CELL - 18 - im.height) // 2), im)
        col = (140, 220, 255, 255) if nfr == 17 else (255, 150, 110, 255)
        dr.text((ox + 4, y0 + 3), "b%d" % b, fill=col)

p = os.path.join(OUT, "compact.png")
img.save(p)
print("->", p, img.size)

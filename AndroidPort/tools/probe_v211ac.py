"""v2.11 batch B: the five zerg building GRPs whose units.dat id is still open,
next to the six whose id is already proven. 6x, tight-cropped, one row per GRP.

This is the iron-rule check (render the sheet, then look at it). The command-card
icon comparison is dead: 4 of 6 known-good controls picked the wrong GRP, because
those 32x32 icons are hand-drawn art rather than scaled-down sprites.

Usage: python probe_v211ac.py
Output: tools/out/v211_bld/identify.png
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out\v211_bld")
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

# (label, grp, frame index) -- the last (most complete) frame of each
WANT = [
    # --- PROVEN, use these as the visual rulers
    ("PROVEN 141 Spire", "unit\\zerg\\spire.grp", -1),
    ("PROVEN 142 Pool", "unit\\zerg\\Snakey.grp", -1),
    ("PROVEN 143 CreepCol", "unit\\zerg\\fcolony.grp", -1),
    ("PROVEN 144 SporeCol", "unit\\zerg\\RCluster.grp", -1),
    ("PROVEN 146 SunkenCol", "unit\\zerg\\SColony.grp", -1),
    ("PROVEN 149 Extract", "unit\\zerg\\Extract.grp", -1),
    ("PROVEN 150 Chrysalis", "unit\\zerg\\chrysal.grp", -1),
    # --- OPEN: 135 HydraliskDen / 136 DefilerMound / 137 GreaterSpire
    #          139 EvolutionChamber / 140 UltraliskCavern
    ("OPEN? MutaCham", "unit\\zerg\\MutaCham.grp", -1),
    ("OPEN? Mutapit", "unit\\zerg\\Mutapit.grp", -1),
    ("OPEN? nest", "unit\\zerg\\nest.grp", -1),
    ("OPEN? NydusPit", "unit\\zerg\\NydusPit.grp", -1),
    ("OPEN? UCereb", "unit\\zerg\\UCereb.grp", -1),
    ("OPEN? cerebrat", "unit\\zerg\\cerebrat.grp", -1),
    ("OPEN? Infest03", "unit\\zerg\\Infest03.grp", -1),
    ("OPEN? ZBuild", "unit\\zerg\\ZBuild.grp", -1),
]

SC = 6
CELL = 340


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def tight(f):
    w, h = f["w"], f["h"]
    src = f["px"]
    x0, y0, x1, y1 = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if src[y * w + x] != 255:
                if x < x0:
                    x0 = x
                if x > x1:
                    x1 = x
                if y < y0:
                    y0 = y
                if y > y1:
                    y1 = y
    if x1 < 0:
        return None
    im = Image.new("RGB", (x1 - x0 + 1, y1 - y0 + 1), (16, 18, 24))
    px = im.load()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            v = src[y * w + x]
            if v != 255:
                px[x - x0, y - y0] = PAL[v]
    return im


cells = []
for label, path, fi in WANT:
    r = load(path)
    if r is None:
        print("MISS %s" % path)
        continue
    t = tight(r[0][fi])
    if t is None:
        print("EMPTY %s" % path)
        continue
    s = min(SC, CELL / float(max(t.width, t.height)))
    im = t.resize((max(1, int(t.width * s)), max(1, int(t.height * s))), Image.NEAREST)
    cells.append((label, im))
    print("%-22s %s  %dx%d -> %dx%d" % (label, os.path.basename(path),
                                        t.width, t.height, im.width, im.height))

PERROW = 4
CW = CELL + 10
CH = CELL + 24
rows = (len(cells) + PERROW - 1) // PERROW
img = Image.new("RGB", (PERROW * CW, rows * CH), (16, 18, 24))
d = ImageDraw.Draw(img)
for k, (label, im) in enumerate(cells):
    x = (k % PERROW) * CW
    y = (k // PERROW) * CH
    d.text((x + 4, y + 4), label, fill=(255, 230, 120))
    img.paste(im, (x + 4 + (CELL - im.width) // 2, y + 20 + (CELL - im.height) // 2))

img.save(os.path.join(OUT, "identify.png"))
print("-> identify.png (%dx%d)" % (img.width, img.height))
PT.close()
SD.close()
BD.close()

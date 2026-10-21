"""v2.11 batch B: every frame of the five unnamed zerg building GRPs, large.

Silhouette matching against the command-card icons is dead (4 of 6 known-good
controls picked the wrong GRP -- those icons are hand-drawn 32x32 art, not
scaled sprites). So this is the iron-rule fallback: put the frames on screen and
look at them.

The question this answers is whether a morph line hides a second building in its
later frames -- the Spire becomes the Greater Spire and the Creep Colony becomes
the Sunken/Spore Colony, so spire.grp may well carry both forms.

Usage: python probe_v211ab.py
Output: tools/out/v211_bld/frames_unnamed.png
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

# short name -> grp, and how many frames to show
WANT = [
    ("spire", "unit\\zerg\\spire.grp", 99),
    ("fcolony", "unit\\zerg\\fcolony.grp", 99),
    ("SColony", "unit\\zerg\\SColony.grp", 99),
    ("RCluster", "unit\\zerg\\RCluster.grp", 99),
    ("hatchery", "unit\\zerg\\hatchery.grp", 99),
    ("Lair", "unit\\zerg\\Lair.grp", 99),
    ("Hive", "unit\\zerg\\Hive.grp", 99),
    ("MutaCham", "unit\\zerg\\MutaCham.grp", 99),
    ("Mutapit", "unit\\zerg\\Mutapit.grp", 99),
    ("UCereb", "unit\\zerg\\UCereb.grp", 99),
    ("nest", "unit\\zerg\\nest.grp", 99),
    ("cerebrat", "unit\\zerg\\cerebrat.grp", 99),
    ("chrysal", "unit\\zerg\\chrysal.grp", 99),
    ("NydusPit", "unit\\zerg\\NydusPit.grp", 99),
    ("Infest03", "unit\\zerg\\Infest03.grp", 99),
    ("ZBuild", "unit\\zerg\\ZBuild.grp", 8),
]

SC = 3
PAD = 8


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def frame_img(f):
    im = Image.new("RGB", (f["w"], f["h"]), (16, 18, 24))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        for x in range(f["w"]):
            v = src[y * f["w"] + x]
            if v != 255:
                px[x, y] = PAL[v]
    bb = im.getbbox()
    if bb is None:
        return im
    # getbbox on an RGB image returns the non-background box, but the background
    # is a dark fill, not black -- use the palette index instead.
    return im


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


rows = []
for short, path, cap in WANT:
    r = load(path)
    if r is None:
        print("MISS %s" % path)
        continue
    frames = r[0][:cap]
    cells = []
    for i, f in enumerate(frames):
        t = tight(f)
        if t is None:
            continue
        cells.append((i, t.resize((max(1, t.width * SC), max(1, t.height * SC)),
                                  Image.NEAREST)))
    rows.append((short, len(r[0]), cells))
    print("%-10s %d frames total, showing %d" % (short, len(r[0]), len(cells)))

rowh = [max([c.height for _, c in cells] + [1]) + 20 for _, _, cells in rows]
maxcells = max(len(cells) for _, _, cells in rows)
colw = 0
for _, _, cells in rows:
    for _, c in cells:
        colw = max(colw, c.width + PAD)

W = colw * maxcells
H = sum(rowh) + 20
img = Image.new("RGB", (W, H), (16, 18, 24))
d = ImageDraw.Draw(img)
y = 0
for (short, total, cells), rh in zip(rows, rowh):
    d.text((4, y + 3), "%s  (%d frames)" % (short, total), fill=(240, 220, 120))
    x = 0
    for i, c in cells:
        img.paste(c, (x, y + 18))
        d.text((x + 2, y + 18), "f%d" % i, fill=(120, 220, 160))
        x += colw
    y += rh

img.save(os.path.join(OUT, "frames_unnamed.png"))
print("-> frames_unnamed.png (%dx%d)" % (img.width, img.height))
PT.close()
SD.close()
BD.close()

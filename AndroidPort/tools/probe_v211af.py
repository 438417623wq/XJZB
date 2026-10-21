"""v2.11 batch B: the four open zerg building ids against every candidate GRP, big.

One row per units.dat id (name from stat_txt.tbl, authoritative), one column per
candidate, and the command-card icon first because that icon is drawn from the
building. 620px cells so the sheet survives the viewer's downscale.

Usage: python probe_v211af.py
Output: tools/out/v211_bld/pick2.png
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

IDS = [(135, "HydraliskDen"), (136, "DefilerMound"),
       (139, "EvolutionChamber"), (140, "UltraliskCavern"),
       # anchors: 138 Queen's Nest and 141 Spire are already settled
       (138, "QueensNest"), (141, "Spire")]

CAND = [("MutaCham", "unit\\zerg\\MutaCham.grp"),
        ("Mutapit", "unit\\zerg\\Mutapit.grp"),
        ("UCereb", "unit\\zerg\\UCereb.grp"),
        ("cerebrat", "unit\\zerg\\cerebrat.grp")]

CELL = 620


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def icon_img(idx):
    f = load("unit\\cmdbtns\\cmdicons.grp")[0][idx]
    im = Image.new("RGB", (f["w"], f["h"]), (250, 250, 250))
    px = im.load()
    for y in range(f["h"]):
        for x in range(f["w"]):
            v = f["px"][y * f["w"] + x]
            if v == 255:
                continue
            if 8 <= v <= 15:
                g = 40 + (v - 8) * 26
                px[x, y] = (g, g, g)
            else:
                px[x, y] = PAL[v]
    bb = None
    for y in range(f["h"]):
        for x in range(f["w"]):
            if px[x, y] != (250, 250, 250):
                bb = [x, y, x, y] if bb is None else [min(bb[0], x), min(bb[1], y),
                                                      max(bb[2], x), max(bb[3], y)]
    if bb:
        im = im.crop((bb[0], bb[1], bb[2] + 1, bb[3] + 1))
    s = CELL / float(max(im.width, im.height))
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.NEAREST)


def sprite_img(path):
    r = load(path)
    if r is None:
        return None
    f = r[0][-1]
    w, h = f["w"], f["h"]
    src = f["px"]
    x0, y0, x1, y1 = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            if src[y * w + x] != 255:
                x0 = min(x0, x)
                x1 = max(x1, x)
                y0 = min(y0, y)
                y1 = max(y1, y)
    if x1 < 0:
        return None
    im = Image.new("RGB", (x1 - x0 + 1, y1 - y0 + 1), (16, 18, 24))
    px = im.load()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            v = src[y * w + x]
            if v != 255:
                px[x - x0, y - y0] = PAL[v]
    s = CELL / float(max(im.width, im.height))
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.NEAREST)


ncol = 1 + len(CAND)
img = Image.new("RGB", (CELL * ncol, (CELL + 34) * len(IDS)), (16, 18, 24))
d = ImageDraw.Draw(img)
for r, (idx, name) in enumerate(IDS):
    y = r * (CELL + 34)
    d.text((6, y + 4), "%d %s" % (idx, name), fill=(255, 230, 120))
    ic = icon_img(idx)
    d.text((6, y + 18), "ICON", fill=(120, 220, 160))
    img.paste(ic, (6 + (CELL - ic.width) // 2, y + 34))
    for c, (cn, cp) in enumerate(CAND):
        sp = sprite_img(cp)
        if sp is None:
            continue
        x = (c + 1) * CELL
        d.text((x + 6, y + 18), cn, fill=(200, 200, 200))
        img.paste(sp, (x + (CELL - sp.width) // 2, y + 34))

img.save(os.path.join(OUT, "pick2.png"))
print("-> pick2.png (%dx%d)" % (img.width, img.height))
PT.close()
SD.close()
BD.close()

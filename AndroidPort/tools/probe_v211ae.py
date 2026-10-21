"""v2.11 batch B: the five open zerg building ids, icon next to each candidate GRP.

The controls say the icon/silhouette IoU is worthless (4 of 6 known-good pairings
lost to RCluster, which is just a big round blob and therefore attracts every
comparison). But two things are solid: the command-card icon *is* drawn from the
building -- icon 149 vs Extract.grp is unmistakable, and icon 138 vs nest.grp
scored 0.84 -- and those 32x32 icons only become readable when they are drawn on
white with the team ramp lifted out of the dark.

So this sheet does the one thing the metric cannot: it puts the icon and every
remaining candidate side by side at a size where a person can say "that one".

Usage: python probe_v211ae.py
Output: tools/out/v211_bld/pick.png
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

# the open ids, with the name stat_txt.tbl gives them
OPEN = [(135, "HydraliskDen"), (136, "DefilerMound"), (137, "GreaterSpire"),
        (139, "EvolutionChamber"), (140, "UltraliskCavern")]

# every zerg building GRP that is not already spoken for
CAND = [("UCereb", "unit\\zerg\\UCereb.grp"),
        ("MutaCham", "unit\\zerg\\MutaCham.grp"),
        ("Mutapit", "unit\\zerg\\Mutapit.grp"),
        ("cerebrat", "unit\\zerg\\cerebrat.grp"),
        ("spire", "unit\\zerg\\spire.grp")]

# two settled rows, drawn the same way, as the ruler for what a match looks like
SETTLED = [(138, "QueensNest", "nest", "unit\\zerg\\nest.grp"),
           (149, "Extractor", "Extract", "unit\\zerg\\Extract.grp"),
           (143, "CreepColony", "fcolony", "unit\\zerg\\fcolony.grp")]

H = 300          # every sprite is scaled to this height
ICON_H = 300


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
    s = ICON_H / float(max(im.width, im.height))
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.NEAREST)


def sprite_img(path, frame=-1):
    r = load(path)
    if r is None:
        return None
    f = r[0][frame]
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
    s = H / float(max(im.width, im.height))
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.NEAREST)


rows = []
for idx, name in OPEN:
    rows.append(("%d %s  (OPEN)" % (idx, name), icon_img(idx),
                 [(cn, sprite_img(cp)) for cn, cp in CAND]))
for idx, name, cn, cp in SETTLED:
    rows.append(("%d %s  (SETTLED = %s)" % (idx, name, cn), icon_img(idx),
                 [(cn, sprite_img(cp))]))

CW = 330
CH = H + 34
ncol = 1 + len(CAND)
img = Image.new("RGB", (CW * ncol, CH * len(rows)), (16, 18, 24))
d = ImageDraw.Draw(img)
for r, (label, ic, cands) in enumerate(rows):
    y = r * CH
    d.text((4, y + 3), label, fill=(255, 230, 120))
    d.text((4, y + 18), "ICON", fill=(120, 220, 160))
    img.paste(ic, (4 + (CW - ic.width) // 2, y + 34))
    for c, (cn, sp) in enumerate(cands):
        x = (c + 1) * CW
        col = (120, 220, 160) if c == 0 else (200, 200, 200)
        d.text((x + 4, y + 18), cn, fill=col)
        if sp is not None:
            img.paste(sp, (x + (CW - sp.width) // 2, y + 34))

img.save(os.path.join(OUT, "pick.png"))
print("-> pick.png (%dx%d)" % (img.width, img.height))
PT.close()
SD.close()
BD.close()

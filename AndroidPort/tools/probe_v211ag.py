"""v2.11 batch B: one open id per image, so nothing gets downscaled away.

The matrix sheets kept getting shrunk by the viewer until the icon was a grey
smudge again. Here each open units.dat id gets its own 1900x430 strip: the
command-card icon (drawn on white, team ramp lifted) then each candidate GRP at
its final frame. Four strips, small enough that every pixel survives.

Usage: python probe_v211ag.py
Output: tools/out/v211_bld/strip_<id>.png
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

CAND = [("MutaCham", "unit\\zerg\\MutaCham.grp"),
        ("Mutapit", "unit\\zerg\\Mutapit.grp"),
        ("UCereb", "unit\\zerg\\UCereb.grp"),
        ("cerebrat", "unit\\zerg\\cerebrat.grp")]

IDS = [(135, "HydraliskDen"), (136, "DefilerMound"),
       (139, "EvolutionChamber"), (140, "UltraliskCavern")]

CELL = 380


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
    s = CELL / float(max(im.width, im.height))
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.NEAREST)


for idx, name in IDS:
    img = Image.new("RGB", (CELL * 5, CELL + 30), (16, 18, 24))
    d = ImageDraw.Draw(img)
    ic = icon_img(idx)
    d.text((6, 4), "%d %s" % (idx, name), fill=(255, 230, 120))
    d.text((6, 18), "ICON (cmdicons %d)" % idx, fill=(120, 220, 160))
    img.paste(ic, (6 + (CELL - ic.width) // 2, 30))
    for c, (cn, cp) in enumerate(CAND):
        sp = sprite_img(cp)
        if sp is None:
            continue
        x = (c + 1) * CELL
        d.text((x + 6, 18), cn, fill=(200, 200, 200))
        img.paste(sp, (x + (CELL - sp.width) // 2, 30))
    p = os.path.join(OUT, "strip_%d.png" % idx)
    img.save(p)
    print("-> strip_%d.png (%dx%d)" % (idx, img.width, img.height))

PT.close()
SD.close()
BD.close()

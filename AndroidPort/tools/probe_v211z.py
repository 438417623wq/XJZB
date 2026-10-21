"""v2.11 batch B: decide the zerg building identities by overlay, not by eye.

Two attempts to name these by looking at them failed. The command-card wireframe
(cmdicons frame N == units.dat id N) is drawn from the same sprite the building
uses, just small, so the honest test is to put the two silhouettes on top of each
other at the wireframe's own size:

    green = wireframe only      red = building sprite only      yellow = both

The true pairing fills with yellow; a wrong one stays green-and-red striped. The
six already-shipping rows run first as the control -- if hatchery/spire/pool/
creep/sunken/extractor do not come out mostly yellow, the method is worthless.

Usage: python probe_v211z.py
Output: tools/out/v211_bld/overlay_id.png
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out\v211_bld")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

# (units.dat id, label, candidate grp, expected)
ROWS = [
    # --- controls: already shipping and provably right
    (131, "Hatchery",      "unit\\zerg\\hatchery.grp", True),
    (141, "Spire",         "unit\\zerg\\spire.grp", True),
    (142, "SpawningPool",  "unit\\zerg\\Snakey.grp", True),
    (143, "CreepColony",   "unit\\zerg\\fcolony.grp", True),
    (146, "SunkenColony",  "unit\\zerg\\SColony.grp", True),
    (149, "Extractor",     "unit\\zerg\\Extract.grp", True),
    # --- the ones batch B must name
    (135, "HydraliskDen",  "unit\\zerg\\UCereb.grp", False),
    (135, "HydraliskDen",  "unit\\zerg\\Mutapit.grp", False),
    (135, "HydraliskDen",  "unit\\zerg\\MutaCham.grp", False),
    (136, "DefilerMound",  "unit\\zerg\\Mutapit.grp", False),
    (136, "DefilerMound",  "unit\\zerg\\MutaCham.grp", False),
    (136, "DefilerMound",  "unit\\zerg\\UCereb.grp", False),
    (139, "EvolutionCham", "unit\\zerg\\MutaCham.grp", False),
    (139, "EvolutionCham", "unit\\zerg\\UCereb.grp", False),
    (139, "EvolutionCham", "unit\\zerg\\Mutapit.grp", False),
    (140, "UltraliskCav",  "unit\\zerg\\UCereb.grp", False),
    (138, "QueensNest",    "unit\\zerg\\nest.grp", False),
    (134, "NydusCanal",    "unit\\zerg\\NydusPit.grp", False),
]

SC = 10
BOX = 40
PERROW = 3
GAP = 14


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def mask_of(f):
    w, h = f["w"], f["h"]
    im = Image.new("L", (w, h), 0)
    px = im.load()
    src = f["px"]
    for y in range(h):
        base = y * w
        for x in range(w):
            if src[base + x] != 255:
                px[x, y] = 255
    bb = im.getbbox()
    return im.crop(bb) if bb else None


def fit(im, box):
    s = box / float(max(im.width, im.height))
    return im.resize((max(1, int(round(im.width * s))),
                      max(1, int(round(im.height * s)))), Image.NEAREST)


def colour(a, b, box=BOX):
    """green = a only, red = b only, yellow = both."""
    ca, cb = fit(a, box), fit(b, box)
    out = Image.new("RGB", (box, box), (16, 18, 24))
    px = out.load()
    pa = ca.load()
    pb = cb.load()
    oa = ((box - ca.width) // 2, (box - ca.height) // 2)
    ob = ((box - cb.width) // 2, (box - cb.height) // 2)
    for y in range(box):
        for x in range(box):
            va = 0 <= x - oa[0] < ca.width and 0 <= y - oa[1] < ca.height and pa[x - oa[0], y - oa[1]] > 127
            vb = 0 <= x - ob[0] < cb.width and 0 <= y - ob[1] < cb.height and pb[x - ob[0], y - ob[1]] > 127
            if va and vb:
                px[x, y] = (230, 220, 90)
            elif va:
                px[x, y] = (70, 220, 110)
            elif vb:
                px[x, y] = (230, 80, 80)
    return out


def frac_both(a, b, box=BOX):
    ca, cb = fit(a, box), fit(b, box)
    pa, pb = ca.load(), cb.load()
    oa = ((box - ca.width) // 2, (box - ca.height) // 2)
    ob = ((box - cb.width) // 2, (box - cb.height) // 2)
    both = union = 0
    for y in range(box):
        for x in range(box):
            va = 0 <= x - oa[0] < ca.width and 0 <= y - oa[1] < ca.height and pa[x - oa[0], y - oa[1]] > 127
            vb = 0 <= x - ob[0] < cb.width and 0 <= y - ob[1] < cb.height and pb[x - ob[0], y - ob[1]] > 127
            if va or vb:
                union += 1
                if va and vb:
                    both += 1
    return both / float(union) if union else 0.0


icons = load("unit\\cmdbtns\\cmdicons.grp")
iframes = icons[0]

cells = []
for idx, label, path, known in ROWS:
    ic = mask_of(iframes[idx])
    r = load(path)
    if ic is None or r is None:
        print("MISS %s %s" % (label, path))
        continue
    bd = mask_of(r[0][0])
    if bd is None:
        print("EMPTY %s" % path)
        continue
    f = frac_both(ic, bd)
    ov = colour(ic, bd)
    ov = ov.resize((ov.width * SC // 2, ov.height * SC // 2), Image.NEAREST)
    cells.append(("%d %s vs %s  both=%.2f%s" % (idx, label, os.path.basename(path), f,
                  "  <-- CONTROL" if known else ""), ov))
    print("%3d %-14s %-18s both=%.3f%s" % (idx, label, os.path.basename(path), f,
          "  (control)" if known else ""))

cw = max(c.width for _, c in cells) + GAP
ch = max(c.height for _, c in cells) + GAP + 16
rows = (len(cells) + PERROW - 1) // PERROW
img = Image.new("RGB", (PERROW * cw, rows * ch), (16, 18, 24))
d = ImageDraw.Draw(img)
for i, (label, c) in enumerate(cells):
    x = (i % PERROW) * cw
    y = (i // PERROW) * ch
    d.text((x + 4, y + 2), label, fill=(240, 220, 120))
    img.paste(c, (x + 4, y + 18))

img.save(os.path.join(OUT, "overlay_id.png"))
print("-> overlay_id.png (%dx%d)" % (img.width, img.height))

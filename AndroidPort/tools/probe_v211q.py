"""v2.11 batch B: name the four unnamed zerg buildings by pairing them with their
command-card wireframe.

The zerg building GRPs in the archives are named for their art (MutaCham,
Mutapit, UCereb, cerebrat, ZBuild) and none of those names says which units.dat
building it is. Guessing from shape alone failed twice -- a purple spire looks
like a purple spire.

The command card is the authority: cmdicons.grp frame index == units.dat unit id
(verified for the terran and protoss rows already), so frame 135 IS the
Hydralisk Den's own wireframe, 136 the Defiler Mound's, 139 the Evolution
Chamber's and 140 the Ultralisk Cavern's. Render icon and candidate side by side
and match them.

The known-good pairs ride along as controls (131/hatchery, 142/Snakey,
143/fcolony, 146/SColony, 149/Extract): if those do not match, the whole
icon-index premise is wrong and nothing below means anything.

Usage: python probe_v211q.py
Output: tools/out/v211_bld/pair_id.png
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

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

# (label, cmdicons frame, building grp path)
PAIRS = [
    # --- controls: already shipping, so a mismatch here invalidates the method
    ("Hatch 131",  131, "unit\\zerg\\hatchery.grp"),
    ("Pool 142",   142, "unit\\zerg\\Snakey.grp"),
    ("Creep 143",  143, "unit\\zerg\\fcolony.grp"),
    ("Sunken 146", 146, "unit\\zerg\\SColony.grp"),
    ("Extract 149", 149, "unit\\zerg\\Extract.grp"),
    ("Spire 141",  141, "unit\\zerg\\spire.grp"),
    # --- the four unnamed ones, each with every surviving candidate
    ("HydraDen 135", 135, "unit\\zerg\\Mutapit.grp"),
    ("HydraDen 135", 135, "unit\\zerg\\MutaCham.grp"),
    ("HydraDen 135", 135, "unit\\zerg\\UCereb.grp"),
    ("HydraDen 135", 135, "unit\\zerg\\cerebrat.grp"),
    ("Defiler 136", 136, "unit\\zerg\\Mutapit.grp"),
    ("Defiler 136", 136, "unit\\zerg\\MutaCham.grp"),
    ("Defiler 136", 136, "unit\\zerg\\UCereb.grp"),
    ("Defiler 136", 136, "unit\\zerg\\cerebrat.grp"),
    ("EvolCham 139", 139, "unit\\zerg\\Mutapit.grp"),
    ("EvolCham 139", 139, "unit\\zerg\\MutaCham.grp"),
    ("EvolCham 139", 139, "unit\\zerg\\UCereb.grp"),
    ("EvolCham 139", 139, "unit\\zerg\\cerebrat.grp"),
    ("UltraCav 140", 140, "unit\\zerg\\Mutapit.grp"),
    ("UltraCav 140", 140, "unit\\zerg\\MutaCham.grp"),
    ("UltraCav 140", 140, "unit\\zerg\\UCereb.grp"),
    ("UltraCav 140", 140, "unit\\zerg\\cerebrat.grp"),
]

SC = 4
PERROW = 4
GAP = 14


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
    return im.crop(bb) if bb else None


icons = load("unit\\cmdbtns\\cmdicons.grp")
if icons is None:
    print("MISS cmdicons")
    sys.exit(1)
iframes, imw, imh = icons

cells = []
for label, idx, path in PAIRS:
    if idx >= len(iframes):
        print("icon miss", label, idx)
        continue
    ic = tight(frame_image(iframes[idx]))
    r = load(path)
    if r is None or ic is None:
        print("MISS %-14s %s" % (label, path))
        continue
    frames, mw, mh = r
    bd = tight(frame_image(frames[0]))
    if bd is None:
        print("EMPTY %-14s %s" % (label, path))
        continue
    # same display height so the silhouettes are directly comparable
    H = 220
    ic = ic.resize((max(1, ic.width * H // ic.height), H), Image.NEAREST)
    bd = bd.resize((max(1, bd.width * H // bd.height), H), Image.NEAREST)
    combo = Image.new("RGBA", (ic.width + bd.width + 12, H), (18, 22, 30, 255))
    combo.paste(ic, (0, 0), ic)
    combo.paste(bd, (ic.width + 12, 0), bd)
    print("%-14s icon%3d %-30s frames=%-3d cell=%dx%d" % (label, idx, path, len(frames), mw, mh))
    cells.append((label + "  " + os.path.basename(path), combo))

cw = max(c.width for _, c in cells) + GAP
ch = max(c.height for _, c in cells) + GAP + 16
rows = (len(cells) + PERROW - 1) // PERROW
img = Image.new("RGBA", (PERROW * cw, rows * ch), (18, 22, 30, 255))
d = ImageDraw.Draw(img)
for i, (label, c) in enumerate(cells):
    x = (i % PERROW) * cw
    y = (i // PERROW) * ch
    d.text((x + 4, y + 2), label, fill=(240, 220, 120, 255))
    img.paste(c, (x + 4, y + 18), c)

img.save(os.path.join(OUT, "pair_id.png"))
print("-> pair_id.png (%dx%d)" % (img.width, img.height))

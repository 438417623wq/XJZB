"""v2.11 batch B: the command-card icons for the zerg buildings, 16x, one per cell.

The silhouettes were unreadable at 10x because the icon art is drawn in the team
ramp (indices 8-15), which renders as dark purple on a dark background. Here each
icon is drawn on white with the team ramp lifted to a readable grey, so the
*drawing* is what you see -- which is the only place the building's shape is
stated in the game's own words.

Usage: python probe_v211ad.py
Output: tools/out/v211_bld/icons_big.png
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

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

# units.dat id -> authoritative name (stat_txt.tbl)
WANT = [
    (131, "Hatchery"), (132, "Lair"), (133, "Hive"),
    (134, "Nydus Canal"), (135, "Hydralisk Den"), (136, "Defiler Mound"),
    (137, "Greater Spire"), (138, "Queen's Nest"), (139, "Evolution Chamber"),
    (140, "Ultralisk Cavern"), (141, "Spire"), (142, "Spawning Pool"),
    (143, "Creep Colony"), (144, "Spore Colony"), (146, "Sunken Colony"),
    (149, "Extractor"), (150, "Mature Crysalis"),
]

SC = 16
CELL = 560


def load(path):
    for ar in (PT, SD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


ic = load("unit\\cmdbtns\\cmdicons.grp")[0]

cells = []
for idx, name in WANT:
    f = ic[idx]
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
                r, gg, b = PAL[v]
                px[x, y] = (r, gg, b)
    # tight crop
    bb = None
    for y in range(f["h"]):
        for x in range(f["w"]):
            if px[x, y] != (250, 250, 250):
                if bb is None:
                    bb = [x, y, x, y]
                else:
                    bb[0] = min(bb[0], x)
                    bb[1] = min(bb[1], y)
                    bb[2] = max(bb[2], x)
                    bb[3] = max(bb[3], y)
    if bb:
        im = im.crop((bb[0], bb[1], bb[2] + 1, bb[3] + 1))
    im = im.resize((im.width * SC, im.height * SC), Image.NEAREST)
    cells.append(("%d %s" % (idx, name), im))
    print("%-4d %-18s %dx%d -> %dx%d" % (idx, name, f["w"], f["h"], im.width, im.height))

PERROW = 3
CW = max(c.width for _, c in cells) + 16
CH = max(c.height for _, c in cells) + 26
rows = (len(cells) + PERROW - 1) // PERROW
img = Image.new("RGB", (PERROW * CW, rows * CH), (250, 250, 250))
d = ImageDraw.Draw(img)
for k, (label, im) in enumerate(cells):
    x = (k % PERROW) * CW
    y = (k // PERROW) * CH
    d.text((x + 4, y + 4), label, fill=(0, 0, 0))
    img.paste(im, (x + 4, y + 20))

img.save(os.path.join(OUT, "icons_big.png"))
print("-> icons_big.png (%dx%d)" % (img.width, img.height))
PT.close()
SD.close()

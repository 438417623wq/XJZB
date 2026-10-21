"""v2.11 batch B/C: horizontal contact sheets, one ROW per unit, one COLUMN per
block, direction 0 only, tight-cropped and 2x.

The vertical `<key>_tight_0_N.png` strips cost one image read each. This packs
four units into one sheet so a whole batch of walk/attack decisions can be made
from two or three images instead of twelve.

The numeric boundary finder (probe_v211h.py) was abandoned: calibrated against
the units whose layout manifest.txt already proves -- zergling walk=[0,1,2]
atk=3, hydra walk=[0,1] atk=2, scv walk=[0,1] atk=2 -- it shows NO loop
distance dip at the cycle length, so it cannot locate the walk/attack seam.
Per the project rule the rendered comparison sheet is the gate.

Usage: python probe_v211i.py <sheetIndex>   (0..2)
Output: tools/out/v211_blocks/sheet_<n>.png
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out\v211_blocks")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

PATHS = {
    "ultra":      "unit\\zerg\\ultra.grp",
    "guardian":   "unit\\zerg\\guardian.grp",
    "defiler":    "unit\\zerg\\defiler.grp",
    "queen":      "unit\\zerg\\queen.grp",
    "lurker":     "unit\\zerg\\lurknorm.grp",
    "lurker_bur": "unit\\zerg\\lurkburr.grp",
    "devourer":   "unit\\zerg\\devour.grp",
    "broodling":  "unit\\zerg\\brood.grp",
    "lurk_egg":   "unit\\zerg\\LurkEgg.grp",
    "medic":      "unit\\terran\\medic.grp",
    "valkyrie":   "unit\\terran\\bomber.grp",
    "spider":     "unit\\terran\\Spider.grp",
}

SHEETS = [
    ["ultra", "queen", "defiler", "lurker"],
    ["devourer", "guardian", "broodling", "lurker_bur"],
    ["medic", "lurk_egg", "valkyrie", "spider"],
]


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def tight(f):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        base = y * f["w"]
        for x in range(f["w"]):
            v = src[base + x]
            if v != 255:
                px[x, y] = PAL[v] + (255,)
    bb = im.getbbox()
    return im.crop(bb) if bb else None


def scale_for(cw):
    # keep one unit row under ~1300px wide so the whole sheet stays legible
    return 2


idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
SC = int(sys.argv[2]) if len(sys.argv) > 2 else 2
keys = SHEETS[idx]

rows = []
for key in keys:
    r = load(PATHS[key])
    if r is None:
        continue
    frames, mw, mh = r
    n = len(frames)
    blocks = (n + 16) // 17
    cells = [tight(frames[b * 17]) for b in range(blocks)]
    cw = max((c.width for c in cells if c is not None), default=1) + 2
    ch = max((c.height for c in cells if c is not None), default=1) + 2
    rows.append((key, blocks, cells, cw, ch))

# At 2x a whole 16-block unit fits on one line. At 3x+ the line would be too
# wide to read after the viewer downscales it, so each unit wraps into several
# lines of at most COLS blocks.
COLS = 16 if SC <= 2 else 8
COLW = (max(r[3] for r in rows)) * SC
LAB = 74

grid_w = min(COLS, max(r[1] for r in rows)) * COLW
sheet_w = LAB + grid_w
sheet_h = sum(((r[1] + COLS - 1) // COLS) * (r[4] * SC + 16) + 8 for r in rows) + 8

img = Image.new("RGBA", (sheet_w, sheet_h), (18, 22, 30, 255))
d = ImageDraw.Draw(img)
y = 4
for key, blocks, cells, cw, ch in rows:
    d.text((2, y + 6), "%s\n%d blocks" % (key, blocks),
           fill=(240, 220, 120, 255))
    for b, c in enumerate(cells):
        x = LAB + (b % COLS) * COLW
        yy = y + (b // COLS) * (ch * SC + 16)
        d.text((x + 2, yy), "b%d" % b, fill=(150, 190, 255, 255))
        if c is None:
            continue
        c = c.resize((c.width * SC, c.height * SC), Image.NEAREST)
        img.paste(c, (x + 2, yy + 14), c)
    y += ((blocks + COLS - 1) // COLS) * (ch * SC + 16) + 8

name = "sheet_%d_x%d.png" % (idx, SC)
img.save(os.path.join(OUT, name))
print("sheet %d x%d: %s -> %s (%dx%d)"
      % (idx, SC, ",".join(keys), name, img.width, img.height))

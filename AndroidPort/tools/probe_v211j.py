"""v2.11 batch B/C: 4x direction-0 grid, all blocks, wrapped into rows.

This is the decision image for the walk/attack seam. probe_v211i.py packs many
units into one sheet but at 2x, where a 128x128 cell holding a 60x60 ultralisk
still reads as a smudge. Here each unit gets a full-width grid of its own:
direction 0 only, tight-cropped, 4x, 8 blocks per row.

What to look for, calibrated on the units manifest.txt already proves
(marine walk=[0,1,2] atk=3, zergling walk=[0,1,2] atk=3, hydra walk=[0,1] atk=2,
zealot walk=[0..4] atk=5, dragoon walk=[0..7] atk=8):
  * a WALK frame repeats a small leg/body cycle, so a late block matches an
    early one;
  * an ATTACK frame is a pose the unit never returns to -- muzzle flash, blade
    thrust, head lunge;
  * the DEATH frames are unmistakable (red blood) and in this pack sit either
    in the final partial block (ultra b15, medic b13) or as a run of full
    blocks (defiler b8..b16), so they are read off the picture, not the index.

Usage: python probe_v211j.py <key>
Output: tools/out/v211_blocks/<key>_d0.png
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
    "marine":     "unit\\terran\\marine.grp",
    "zealot":     "unit\\protoss\\zealot.grp",
}

SC = 4
COLS = 8


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


key = sys.argv[1]
r = load(PATHS[key])
if r is None:
    print("MISS", key)
    sys.exit(1)
frames, mw, mh = r
n = len(frames)
blocks = (n + 16) // 17

cells = [tight(frames[b * 17]) for b in range(blocks)]
cw = max((c.width for c in cells if c is not None), default=1) + 2
ch = max((c.height for c in cells if c is not None), default=1) + 2
cw *= SC
ch *= SC

rows = (blocks + COLS - 1) // COLS
lab = 60
img = Image.new("RGBA", (lab + COLS * cw, rows * (ch + 16)), (18, 22, 30, 255))
d = ImageDraw.Draw(img)
for b, c in enumerate(cells):
    gx = b % COLS
    gy = b // COLS
    x = lab + gx * cw
    y = gy * (ch + 16)
    d.text((x + 2, y), "b%d" % b, fill=(240, 220, 120, 255))
    if c is None:
        continue
    c = c.resize((c.width * SC, c.height * SC), Image.NEAREST)
    img.paste(c, (x + 2, y + 14), c)
d.text((2, 4), "%s\n%d blocks\ndir 0" % (key, blocks), fill=(150, 200, 255, 255))
name = "%s_d0.png" % key
img.save(os.path.join(OUT, name))
print("%-11s blocks=%-3d -> %s (%dx%d)" % (key, blocks, name, img.width, img.height))

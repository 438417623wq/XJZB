"""v2.11 batch B/C: tight-cropped block strips.

The plain strips (probe_v211b/c) paste each frame into its full cell, so a
128x128 cell holding a 60x60 ultralisk wastes most of the canvas and the whole
strip gets downscaled into mush. This crops every frame to its non-transparent
bounding box first, which roughly doubles the effective zoom at the same output
width and is what makes the walk/attack split actually readable.

Layout: one ROW per block (b0..bN), one COLUMN per sampled direction.
Output: tools/out/v211_blocks/<key>_tight.png
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
    "zergling":   "unit\\zerg\\zergling.grp",
    "hydra":      "unit\\zerg\\hydra.grp",
    "muta":       "unit\\zerg\\mutalid.grp",
}


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


def tight(f):
    im = frame_image(f)
    bb = im.getbbox()
    return im.crop(bb) if bb else None


key = sys.argv[1]
dirs = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [0, 4, 8, 12]
scale = int(sys.argv[3]) if len(sys.argv) > 3 else 2

r = load(PATHS[key])
if r is None:
    print("MISS", key)
    sys.exit(1)
frames, mw, mh = r
n = len(frames)
blocks = (n + 16) // 17

# optional 4th/5th args narrow the block range so a 16-block sheet can be
# split across two legible images instead of one that the viewer shrinks.
b_first = int(sys.argv[4]) if len(sys.argv) > 4 else 0
b_last = int(sys.argv[5]) if len(sys.argv) > 5 else blocks - 1
b_first = max(0, min(b_first, blocks - 1))
b_last = max(b_first, min(b_last, blocks - 1))
block_range = list(range(b_first, b_last + 1))

# measure the widest/tallest cropped frame so every cell can share one size
cells = {}
cw = ch = 0
for b in block_range:
    for dd in dirs:
        fi = b * 17 + dd
        if fi >= n:
            continue
        im = tight(frames[fi])
        cells[(b, dd)] = im
        if im is not None:
            cw = max(cw, im.width)
            ch = max(ch, im.height)

cw = (cw + 4) * scale
ch = (ch + 4) * scale
lab = 30
img = Image.new("RGBA", (lab + len(dirs) * cw, len(block_range) * ch),
                (22, 26, 34, 255))
d = ImageDraw.Draw(img)
for row, b in enumerate(block_range):
    d.text((2, row * ch + ch // 2), "b%d" % b, fill=(240, 220, 120, 255))
    for k, dd in enumerate(dirs):
        im = cells.get((b, dd))
        if im is None:
            continue
        if scale != 1:
            im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        img.paste(im, (lab + k * cw + 2 * scale, row * ch + 2 * scale), im)
name = "%s_tight_%d_%d.png" % (key, b_first, b_last)
img.save(os.path.join(OUT, name))
print("%-12s n=%d blocks=%d range=%d..%d dirs=%s -> %s (%dx%d)"
      % (key, n, blocks, b_first, b_last, dirs, name, img.width, img.height))

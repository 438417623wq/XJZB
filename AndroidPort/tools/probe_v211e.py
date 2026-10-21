"""v2.11 batch B/C: transposed block grid -- one COLUMN per block, directions
as ROWS.

probe_v211c.py stacked blocks as rows, which makes tall images (ultra: 2048 px)
that get downscaled into mush. Transposing puts the block count on the X axis,
so a 16-block unit becomes a wide-but-short strip that survives downscaling and
lets every block be compared side by side in one glance.

Rows are directions 0/4/8/12 (the four cardinal-ish facings); columns are
blocks b0..bN, labelled along the top.

Usage:  python probe_v211e.py <key> [scale]
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
    "muta":       "unit\\zerg\\mutalid.grp",
    "zergling":   "unit\\zerg\\zergling.grp",
    "hydra":      "unit\\zerg\\hydra.grp",
    "scv":        "unit\\terran\\SCV.grp",
}

DIRS = [0, 4, 8, 12]


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def frame_image(f, scale):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        base = y * f["w"]
        for x in range(f["w"]):
            v = src[base + x]
            if v != 255:
                px[x, y] = PAL[v] + (255,)
    if scale != 1:
        im = im.resize((f["w"] * scale, f["h"] * scale), Image.NEAREST)
    return im


key = sys.argv[1]
scale = int(sys.argv[2]) if len(sys.argv) > 2 else 1
r = load(PATHS[key])
if r is None:
    print("MISS", key)
    sys.exit(1)
frames, mw, mh = r
n = len(frames)
blocks = (n + 16) // 17

cw, ch = mw * scale, mh * scale
top = 16
img = Image.new("RGBA", (blocks * cw, top + len(DIRS) * ch), (22, 26, 34, 255))
d = ImageDraw.Draw(img)
for b in range(blocks):
    d.text((b * cw + 2, 2), "b%d" % b, fill=(240, 220, 120, 255))
    for k, dd in enumerate(DIRS):
        fi = b * 17 + dd
        if fi >= n:
            continue
        im = frame_image(frames[fi], scale)
        img.paste(im, (b * cw, top + k * ch), im)
name = "%s_t.png" % key
img.save(os.path.join(OUT, name))
print("%-12s n=%d blocks=%d -> %s (%dx%d)"
      % (key, n, blocks, name, img.width, img.height))

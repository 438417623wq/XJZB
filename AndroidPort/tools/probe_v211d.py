"""v2.11 batch B/C: 2x-zoomed 4-direction block strips, a few blocks per image.

probe_v211c.py proved the block convention against the marine ruler (b0..b2
walk, b3 attack, b13 death) but at 1x the small cells are hard to read. This
zooms 2x and splits the block range into chunks so each image stays legible
after the viewer downscales it.

Usage:  python probe_v211d.py <key> <firstBlock> <lastBlock>
        python probe_v211d.py medic 0 6
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
}


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
b0 = int(sys.argv[2])
b1 = int(sys.argv[3])
scale = int(sys.argv[4]) if len(sys.argv) > 4 else 2
DIRS = [0, 4, 8, 12]

r = load(PATHS[key])
if r is None:
    print("MISS", key)
    sys.exit(1)
frames, mw, mh = r
n = len(frames)
blocks = (n + 16) // 17
b1 = min(b1, blocks - 1)

cw, ch = mw * scale, mh * scale
lab = 30
img = Image.new("RGBA", (lab + len(DIRS) * cw, (b1 - b0 + 1) * ch),
                (22, 26, 34, 255))
d = ImageDraw.Draw(img)
for b in range(b0, b1 + 1):
    row = b - b0
    d.text((2, row * ch + ch // 2), "b%d" % b, fill=(240, 220, 120, 255))
    for k, dd in enumerate(DIRS):
        fi = b * 17 + dd
        if fi >= n:
            continue
        im = frame_image(frames[fi], scale)
        img.paste(im, (lab + k * cw, row * ch), im)
name = "%s_b%d_%d.png" % (key, b0, b1)
img.save(os.path.join(OUT, name))
print("%s blocks %d..%d of %d -> %s (%dx%d)"
      % (key, b0, b1, blocks, name, img.width, img.height))

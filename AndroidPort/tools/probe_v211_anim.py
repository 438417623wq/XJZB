"""v2.11 batch B/C: one direction, all blocks in a row, on the FULL cell.

The tight-cropped sheets (probe_v211g) normalise away the frame's x/y offset,
which hides exactly the thing that distinguishes a walk cycle from a set of
near-identical poses: a body bob, a lean, a lunge. Here every frame is pasted
at its real offset inside the cell, so the row reads as a film strip of the
animation.

Tight-cropping also hides nothing about the silhouette, so this is the image
that answers "is there a pose the unit never returns to" (attack) and "does an
early block come back around" (walk).

Usage: python probe_v211_anim.py <key> [dir] [scale]
Output: tools/out/v211_blocks/<key>_anim_d<dir>.png
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
    "guardian":   "unit\\zerg\\guardian.grp",
    "lurker":     "unit\\zerg\\lurknorm.grp",
    "lurker_bur": "unit\\zerg\\lurkburr.grp",
    "devourer":   "unit\\zerg\\devour.grp",
    "marine":     "unit\\terran\\marine.grp",
    "zealot":     "unit\\protoss\\zealot.grp",
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


key = sys.argv[1]
dd = int(sys.argv[2]) if len(sys.argv) > 2 else 0
SC = int(sys.argv[3]) if len(sys.argv) > 3 else 3

r = load(PATHS[key])
if r is None:
    print("MISS", key)
    sys.exit(1)
frames, mw, mh = r
n = len(frames)
blocks = (n + 16) // 17

cw, ch = mw * SC, mh * SC
lab = 26
img = Image.new("RGBA", (lab + blocks * (cw + 4), ch + 20), (18, 22, 30, 255))
d = ImageDraw.Draw(img)
for b in range(blocks):
    fi = b * 17 + dd
    if fi >= n:
        continue
    im = frame_image(frames[fi]).resize((cw, ch), Image.NEAREST)
    x = lab + b * (cw + 4)
    d.text((x + 2, 2), "b%d" % b, fill=(240, 220, 120, 255))
    img.paste(im, (x, 18), im)

name = "%s_anim_d%d.png" % (key, dd)
img.save(os.path.join(OUT, name))
print("%-11s n=%d blocks=%d cell=%dx%d dir=%d scale=%d -> %s (%dx%d)"
      % (key, n, blocks, mw, mh, dd, SC, name, img.width, img.height))

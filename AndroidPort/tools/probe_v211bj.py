"""v2.11: DECIDE the GRP frame ordering (animation-major vs direction-major).

The pipeline assumes animation-major:
    frame index = animationFrame * 17 + direction
so `walk_blocks` counts ANIMATION FRAMES and each block is one pose seen from
all 17 facings.

The alternative is direction-major:
    frame index = direction * framesPerDirection + animationFrame
in which case raw frames 0..16 would be 17 successive animation frames of
direction 0, and `walk_blocks` would be meaningless.

This draws raw frames 0..50 as three rows of 17, with NO tight cropping, so a
rotation (animation-major) is unmistakable: in a rotation row the unit's facing
sweeps around the compass and each row looks like the one above it. In a
progression row the facing stays put and only the pose changes.

Usage: python probe_v211bj.py <key> [cell]
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "v211_unit")
os.makedirs(OUT, exist_ok=True)

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

PATHS = {
    "marine": "unit\\terran\\marine.grp",
    "scv": "unit\\terran\\SCV.grp",
    "ultra": "unit\\zerg\\ultra.grp",
    "queen": "unit\\zerg\\queen.grp",
}

key = sys.argv[1]
CELL = int(sys.argv[2]) if len(sys.argv) > 2 else 210
NROW = 3


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def frame_image(f):
    return Image.frombytes  # placeholder


def fimg(f):
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


res = load(PATHS[key])
frames, mw, mh = res
W = 17 * CELL
H = 24 + NROW * CELL
img = Image.new("RGBA", (W, H), (16, 16, 22, 255))
dr = ImageDraw.Draw(img)
dr.text((6, 6), "%s  raw frames 0..%d in rows of 17   cell=%dx%d  total=%d"
        % (key, NROW * 17 - 1, mw, mh, len(frames)), fill=(255, 235, 140, 255))
for r in range(NROW):
    for c in range(17):
        i = r * 17 + c
        if i >= len(frames):
            break
        im = fimg(frames[i])
        sc = min((CELL - 8) / max(1, im.width), (CELL - 8) / max(1, im.height))
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))),
                       Image.NEAREST)
        ox = c * CELL
        oy = 24 + r * CELL
        img.paste(im, (ox + (CELL - im.width) // 2,
                       oy + (CELL - im.height) // 2), im)
        dr.text((ox + 4, oy + 2), "%d" % i, fill=(140, 220, 255, 255))
    dr.text((4, 24 + r * CELL + CELL - 14), "row %d" % r, fill=(255, 200, 120, 255))

p = os.path.join(OUT, "layout_%s.png" % key)
img.save(p)
print("->", p, img.size)

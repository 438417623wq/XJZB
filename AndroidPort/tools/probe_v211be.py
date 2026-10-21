"""v2.11: DECIDE the GRP frame order empirically.

Two candidate layouts:
  A) animation-major: frame index = animFrame*17 + direction
     -> raw frames 0..16 are ONE animation frame seen from the 17 facings,
        i.e. a smooth rotation.
  B) direction-major: frame index = direction*N + animFrame
     -> raw frames 0..16 are 17 successive ANIMATION frames of direction 0,
        i.e. a walk/attack/death progression at a fixed facing.

This renders raw frames 0..16 of one unit in one big row so the difference is
unmistakable: a rotation sweeps around, a progression changes pose.

Usage: python probe_v211be.py <key> [cell]
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
    "ultra": "unit\\zerg\\ultra.grp",
    "scv": "unit\\terran\\SCV.grp",
}

CELL = int(sys.argv[2]) if len(sys.argv) > 2 else 300
N = 17


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
    return im.crop(bb) if bb else im


key = sys.argv[1]
res = load(PATHS[key])
frames, mw, mh = res
W = N * CELL
H = CELL + 30
img = Image.new("RGBA", (W, H), (16, 16, 22, 255))
dr = ImageDraw.Draw(img)
dr.text((6, 8), "%s raw frames 0..%d   cell %dx%d   total=%d frames"
        % (key, N - 1, mw, mh, len(frames)), fill=(255, 235, 140, 255))
for i in range(N):
    im = frame_image(frames[i])          # NO tight crop: keep the anchor
    sc = min((CELL - 16) / max(1, im.width), (CELL - 16) / max(1, im.height))
    im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))),
                   Image.NEAREST)
    ox = i * CELL
    img.paste(im, (ox + (CELL - im.width) // 2,
                   30 + (CELL - im.height) // 2), im)
    dr.text((ox + 5, 12), "%d" % i, fill=(140, 220, 255, 255))
p = os.path.join(OUT, "order_%s.png" % key)
img.save(p)
print("->", p, img.size)

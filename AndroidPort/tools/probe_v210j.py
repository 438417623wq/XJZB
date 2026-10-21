"""v2.10 probe 10: decide the frame layout of a protoss unit GRP.

Two competing readings of "n = 17*k + tail":
  block-major   frames b*17..b*17+16 are the 17 directions of animation frame b
  dir-major     frames d*(W+A)..+W+A-1 are direction d's animation frames

Render the same frame set both ways and the correct one is obvious: under
block-major, frames 0..16 are one pose rotating; under dir-major they are one
direction animating.
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out\v210_layout")
os.makedirs(OUT, exist_ok=True)
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
BASE_PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

CASES = [
    ("zealot", "unit\\protoss\\zealot.grp", 3),
    ("dragoon", "unit\\protoss\\dragoon.grp", 2),
    ("marine", "unit\\terran\\marine.grp", 3),
    ("scv", "unit\\terran\\SCV.grp", 3),
]


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
                px[x, y] = BASE_PAL[v] + (255,)
    return im


for name, path, z in CASES:
    r = load(path)
    if r is None:
        print("MISS", name)
        continue
    frames, mw, mh = r
    n = len(frames)
    idx = list(range(17))
    cw, ch = mw * z + 8, mh * z + 22
    img = Image.new("RGBA", (len(idx) * cw + 8, ch + 8), (22, 26, 34, 255))
    d = ImageDraw.Draw(img)
    for k, fi in enumerate(idx):
        f = frames[fi]
        im = frame_image(f).resize((f["w"] * z, f["h"] * z), Image.NEAREST)
        img.paste(im, (4 + k * cw + (mw * z - f["w"] * z) // 2,
                       4 + (mh * z - f["h"] * z) // 2), im)
        d.text((4 + k * cw + 2, ch - 16), "%d" % fi, fill=(170, 210, 240, 255))
    p = os.path.join(OUT, name + "_frames0_16.png")
    img.save(p)
    print("%-9s n=%-4d frames0_16 %dx%d" % (name, n, img.width, img.height))

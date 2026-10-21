"""v2.10 probe 13: settle block-major vs direction-major frame layout.

Two candidate layouts for a unit GRP:
  block-major      frames b*17+d = animation frame b, direction d
                   => frames 0..16 are ONE pose seen from 17 directions
                   => frames 0,17,34,... are the animation of direction 0
  direction-major  frames d*K+f = direction d, animation frame f (K frames each)
                   => frames 0..K-1 are ONE direction animating

Renders both readings side by side, plus the death tail (which cannot be a set
of directions -- a death is a time sequence), so the truth is visible.
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out\v210_layout2")
os.makedirs(OUT, exist_ok=True)
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
BASE_PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]


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


def row(path, idx, label, z=3, title=""):
    r = load(path)
    if r is None:
        print("MISS", label)
        return None
    frames, mw, mh = r
    n = len(frames)
    cw, ch = mw * z + 8, mh * z + 30
    img = Image.new("RGBA", (len(idx) * cw + 8, ch + 8), (22, 26, 34, 255))
    d = ImageDraw.Draw(img)
    d.text((6, 2), title, fill=(255, 230, 130, 255))
    for k, fi in enumerate(idx):
        if fi >= n:
            continue
        f = frames[fi]
        im = frame_image(f).resize((f["w"] * z, f["h"] * z), Image.NEAREST)
        img.paste(im, (4 + k * cw + (mw * z - f["w"] * z) // 2,
                       18 + (mh * z - f["h"] * z) // 2), im)
        d.text((4 + k * cw + 2, ch - 14), str(fi), fill=(170, 210, 240, 255))
    p = os.path.join(OUT, label + ".png")
    img.save(p)
    print("%-26s %dx%d" % (label, img.width, img.height))
    return img


ZEALOT = "unit\\protoss\\zealot.grp"
MARINE = "unit\\terran\\marine.grp"
ZERGLING = "unit\\zerg\\zergling.grp"

row(ZEALOT, list(range(0, 17)),
    "zealot_frames0_16", 2, "zealot frames 0..16  (block-major => 17 directions)")
row(ZEALOT, list(range(0, 13)),
    "zealot_frames0_12", 3, "zealot frames 0..12  (dir-major => dir0 animation)")
row(ZEALOT, [0, 17, 34, 51, 68, 85, 102, 119, 136, 153, 170, 187, 204],
    "zealot_blockmajor_anim", 3, "zealot frames 0,17,34.. (block-major => dir0 animation)")
row(ZEALOT, [221, 222, 223, 224, 225, 226, 227],
    "zealot_tail", 3, "zealot frames 221..227 (tail)")
row(ZERGLING, [289, 290, 291, 292, 293, 294, 295],
    "zergling_tail", 3, "zergling frames 289..295 (tail)")
row(MARINE, [221, 222, 223, 224, 225, 226, 227, 228],
    "marine_tail", 3, "marine frames 221..228 (tail)")
row(MARINE, list(range(0, 13)),
    "marine_frames0_12", 3, "marine frames 0..12")
row(MARINE, [0, 17, 34, 51, 68, 85, 102, 119, 136, 153, 170, 187, 204],
    "marine_blockmajor_anim", 3, "marine frames 0,17,34..")

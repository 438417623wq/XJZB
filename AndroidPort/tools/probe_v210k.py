"""v2.10 probe 11: settle the GRP frame layout question.

Take ONE block (17 consecutive frames) of a known-good unit and render it as a
single row at high zoom. If the 17 frames are the 17 directions of one pose, the
row is one pose rotating (=> block-major, which is what v2.8 shipped). If they
are 17 time steps, the row is one direction animating.
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
    ("marine_b0", "unit\\terran\\marine.grp", 0, 3),
    ("marine_b3", "unit\\terran\\marine.grp", 3, 3),
    ("zealot_b0", "unit\\protoss\\zealot.grp", 0, 3),
    ("zealot_b4", "unit\\protoss\\zealot.grp", 4, 3),
    ("zealot_b5", "unit\\protoss\\zealot.grp", 5, 3),
    ("zergling_b0", "unit\\zerg\\zergling.grp", 0, 3),
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


for name, path, block, z in CASES:
    r = load(path)
    if r is None:
        print("MISS", name)
        continue
    frames, mw, mh = r
    n = len(frames)
    cw, ch = mw * z + 8, mh * z + 22
    img = Image.new("RGBA", (17 * cw + 8, ch + 8), (22, 26, 34, 255))
    d = ImageDraw.Draw(img)
    for k in range(17):
        fi = block * 17 + k
        if fi >= n:
            continue
        f = frames[fi]
        im = frame_image(f).resize((f["w"] * z, f["h"] * z), Image.NEAREST)
        img.paste(im, (4 + k * cw + (mw * z - f["w"] * z) // 2,
                       4 + (mh * z - f["h"] * z) // 2), im)
        d.text((4 + k * cw + 2, ch - 16), "%d" % k, fill=(170, 210, 240, 255))
    p = os.path.join(OUT, name + ".png")
    img.save(p)
    print("%-12s %dx%d" % (name, img.width, img.height))

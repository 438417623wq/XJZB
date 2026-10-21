"""v2.10 probe 5: per-unit block strips at native size (one file each) so the
walk/attack block split can be read directly off the images."""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out\v210_blocks")
os.makedirs(OUT, exist_ok=True)
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
BASE_PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

UNITS = [
    ("zealot", "unit\\protoss\\zealot.grp"),
    ("dragoon", "unit\\protoss\\dragoon.grp"),
    ("templar", "unit\\protoss\\templar.grp"),
    ("dtemplar", "unit\\protoss\\dtemplar.grp"),
    ("scout", "unit\\protoss\\scout.grp"),
    ("corsair", "unit\\protoss\\corsair.grp"),
    ("reaver", "unit\\protoss\\trilob.grp"),
    ("arbiter", "unit\\protoss\\arbiter.grp"),
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


for name, path in UNITS:
    r = load(path)
    if r is None:
        print("MISS", name)
        continue
    frames, mw, mh = r
    n = len(frames)
    nb = (n + 16) // 17
    cw, ch = mw + 6, mh + 20
    img = Image.new("RGBA", (nb * cw + 8, ch + 8), (22, 26, 34, 255))
    d = ImageDraw.Draw(img)
    for b in range(nb):
        fi = b * 17 + 8
        if fi >= n:
            fi = n - 1
        f = frames[fi]
        im = frame_image(f)
        ox = 4 + b * cw + (mw - f["w"]) // 2
        oy = 4 + (mh - f["h"]) // 2
        img.paste(im, (ox, oy), im)
        cnt = min(17, n - b * 17)
        d.text((4 + b * cw + 2, ch - 14), "b%d/%d" % (b, cnt),
               fill=(160, 200, 230, 255))
    p = os.path.join(OUT, name + ".png")
    img.save(p)
    print("%-10s %dx%d" % (name, img.width, img.height))

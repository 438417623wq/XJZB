"""v2.10 probe 9: render the *in-game* unit sheet for each protoss unit -- one
row per 17-direction block, columns = directions -- so the walk rows and the
attack row(s) can be told apart exactly the way the game will draw them.
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out\v210_sheets")
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
    ("reaver", "unit\\protoss\\trilob.grp"),
    ("corsair", "unit\\protoss\\corsair.grp"),
    ("scout", "unit\\protoss\\scout.grp"),
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
    img = Image.new("RGBA", (17 * mw, nb * mh), (22, 26, 34, 255))
    d = ImageDraw.Draw(img)
    for b in range(nb):
        for dd in range(17):
            fi = b * 17 + dd
            if fi >= n:
                continue
            f = frames[fi]
            im = frame_image(f)
            img.paste(im, (dd * mw + f["x"], b * mh + f["y"]), im)
        d.text((2, b * mh + 2), "b%d" % b, fill=(255, 230, 120, 255))
    p = os.path.join(OUT, name + ".png")
    img.save(p)
    print("%-10s blocks=%-3d sheet=%dx%d" % (name, nb, img.width, img.height))

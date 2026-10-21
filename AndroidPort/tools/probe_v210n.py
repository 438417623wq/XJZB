"""v2.10 probe 14: high-zoom south-facing strip, one cell per 17-frame block,
wrapped a few per row. At zoom 6 the pose differences that separate a walk
cycle from an attack sequence are legible.
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out\v210_rows6")
os.makedirs(OUT, exist_ok=True)
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
BASE_PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

UNITS = [
    ("probe", "unit\\protoss\\probe.grp", 1, 4),
    ("zealot", "unit\\protoss\\zealot.grp", 1, 4),
    ("dragoon", "unit\\protoss\\dragoon.grp", 1, 4),
    ("templar", "unit\\protoss\\templar.grp", 1, 4),
    ("dtemplar", "unit\\protoss\\dtemplar.grp", 1, 4),
    ("archon", "unit\\protoss\\archon.grp", 1, 2),
    ("darchon", "unit\\protoss\\darchn.grp", 1, 2),
    ("shuttle", "unit\\protoss\\shuttle.grp", 1, 2),
    ("scout", "unit\\protoss\\scout.grp", 1, 2),
    ("arbiter", "unit\\protoss\\arbiter.grp", 1, 2),
    ("carrier", "unit\\protoss\\carrier.grp", 1, 2),
    ("intercep", "unit\\protoss\\Intercep.grp", 1, 2),
    ("reaver", "unit\\protoss\\trilob.grp", 1, 4),
    ("observer", "unit\\protoss\\witness.grp", 1, 2),
    ("corsair", "unit\\protoss\\corsair.grp", 1, 4),
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


Z = 6
for name, path, _z, per_row in UNITS:
    r = load(path)
    if r is None:
        print("MISS", name)
        continue
    frames, mw, mh = r
    n = len(frames)
    nb = (n + 16) // 17
    cw, ch = mw * Z + 10, mh * Z + 28
    rows = (nb + per_row - 1) // per_row
    img = Image.new("RGBA", (per_row * cw + 8, rows * ch + 8), (22, 26, 34, 255))
    d = ImageDraw.Draw(img)
    for b in range(nb):
        fi = b * 17 + 8
        if fi >= n:
            fi = n - 1
        f = frames[fi]
        im = frame_image(f).resize((f["w"] * Z, f["h"] * Z), Image.NEAREST)
        cx = (b % per_row) * cw
        cy = (b // per_row) * ch
        img.paste(im, (4 + cx + (mw * Z - f["w"] * Z) // 2,
                       4 + cy + (mh * Z - f["h"] * Z) // 2), im)
        cnt = min(17, n - b * 17)
        d.text((4 + cx + 4, cy + ch - 20), "b%d len%d" % (b, cnt),
               fill=(180, 220, 250, 255))
    p = os.path.join(OUT, name + ".png")
    img.save(p)
    print("%-10s blocks=%-3d %dx%d" % (name, nb, img.width, img.height))

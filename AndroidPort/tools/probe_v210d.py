"""v2.10 probe 4: one compact strip per protoss unit -- the south-facing frame
(direction 8) of every 17-frame block, labelled with the block index and frame
count. This is what decides the walk/attack block split for pipeline_sprites.py.
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out")
os.makedirs(OUT, exist_ok=True)
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
BASE_PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

UNITS = [
    ("probe", "unit\\protoss\\probe.grp"),
    ("zealot", "unit\\protoss\\zealot.grp"),
    ("dragoon", "unit\\protoss\\dragoon.grp"),
    ("templar", "unit\\protoss\\templar.grp"),
    ("dtemplar", "unit\\protoss\\dtemplar.grp"),
    ("archon", "unit\\protoss\\archon.grp"),
    ("darchon", "unit\\protoss\\darchn.grp"),
    ("scout", "unit\\protoss\\scout.grp"),
    ("arbiter", "unit\\protoss\\arbiter.grp"),
    ("carrier", "unit\\protoss\\carrier.grp"),
    ("intercep", "unit\\protoss\\Intercep.grp"),
    ("reaver", "unit\\protoss\\trilob.grp"),
    ("corsair", "unit\\protoss\\corsair.grp"),
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


def strip(name, path):
    r = load(path)
    if r is None:
        print("MISS", name)
        return None
    frames, mw, mh = r
    n = len(frames)
    nb = (n + 16) // 17
    cw, ch = mw + 6, mh + 18
    img = Image.new("RGBA", (nb * cw + 76, ch + 8), (22, 26, 34, 255))
    d = ImageDraw.Draw(img)
    d.text((4, ch // 2), name, fill=(240, 220, 150, 255))
    for b in range(nb):
        fi = b * 17 + 8
        if fi >= n:
            fi = n - 1
        f = frames[fi]
        im = frame_image(f)
        ox = 76 + b * cw + (mw - f["w"]) // 2
        oy = 4 + (mh - f["h"]) // 2
        img.paste(im, (ox, oy), im)
        cnt = min(17, n - b * 17)
        d.text((76 + b * cw + 2, ch - 12), "b%d/%d" % (b, cnt),
               fill=(160, 200, 230, 255))
    return img


strips = [s for s in (strip(n, p) for n, p in UNITS) if s is not None]
W = max(s.width for s in strips)
H = sum(s.height for s in strips)
sheet = Image.new("RGBA", (W, H), (18, 20, 26, 255))
y = 0
for s in strips:
    sheet.paste(s, (0, y))
    y += s.height
p = os.path.join(OUT, "v210_block_strips.png")
sheet.save(p)
print("wrote", p, sheet.width, "x", sheet.height)

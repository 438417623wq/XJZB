"""v2.10 probe 7: wrap the dir-8 block strip onto several rows so the whole
unit fits inside the 8192px image limit, at a zoom that keeps poses readable.

Output: tools/out/v210_rows/<name>.png -- one cell per 17-frame block, labelled
"bN/len", direction 8 (south) so every block is seen from the same angle.
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out\v210_rows")
os.makedirs(OUT, exist_ok=True)
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
BASE_PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

UNITS = [
    ("probe", "unit\\protoss\\probe.grp", 3, 6),
    ("zealot", "unit\\protoss\\zealot.grp", 2, 5),
    ("dragoon", "unit\\protoss\\dragoon.grp", 2, 6),
    ("templar", "unit\\protoss\\templar.grp", 2, 5),
    ("dtemplar", "unit\\protoss\\dtemplar.grp", 2, 6),
    ("archon", "unit\\protoss\\archon.grp", 2, 2),
    ("darchon", "unit\\protoss\\darchn.grp", 2, 2),
    ("shuttle", "unit\\protoss\\shuttle.grp", 2, 2),
    ("scout", "unit\\protoss\\scout.grp", 3, 2),
    ("arbiter", "unit\\protoss\\arbiter.grp", 2, 2),
    ("carrier", "unit\\protoss\\carrier.grp", 1, 2),
    ("intercep", "unit\\protoss\\Intercep.grp", 4, 2),
    ("reaver", "unit\\protoss\\trilob.grp", 2, 5),
    ("observer", "unit\\protoss\\witness.grp", 3, 2),
    ("corsair", "unit\\protoss\\corsair.grp", 3, 5),
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


for name, path, z, per_row in UNITS:
    r = load(path)
    if r is None:
        print("MISS", name)
        continue
    frames, mw, mh = r
    n = len(frames)
    nb = (n + 16) // 17
    cw, ch = mw * z + 8, mh * z + 24
    rows = (nb + per_row - 1) // per_row
    img = Image.new("RGBA", (per_row * cw + 8, rows * ch + 8), (22, 26, 34, 255))
    d = ImageDraw.Draw(img)
    for b in range(nb):
        fi = b * 17 + 8
        if fi >= n:
            fi = n - 1
        f = frames[fi]
        im = frame_image(f).resize((f["w"] * z, f["h"] * z), Image.NEAREST)
        cx = (b % per_row) * cw
        cy = (b // per_row) * ch
        ox = 4 + cx + (mw * z - f["w"] * z) // 2
        oy = 4 + cy + (mh * z - f["h"] * z) // 2
        img.paste(im, (ox, oy), im)
        cnt = min(17, n - b * 17)
        d.text((4 + cx + 2, cy + ch - 16), "b%d/%d" % (b, cnt),
               fill=(170, 210, 240, 255))
    p = os.path.join(OUT, name + ".png")
    img.save(p)
    print("%-10s n=%-4d blocks=%-3d zoom=%d %dx%d" % (name, n, nb, z, img.width, img.height))

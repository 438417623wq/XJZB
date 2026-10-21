"""v2.11 batch B/C: render every 17-frame block of the new unit GRPs as a
labelled strip so the walk/attack/death split is read off the pictures.

This is the step the protoss round proved non-optional: probe_v210a.py's
numbers said "5 blocks" for the zealot and it took rendering them to see that
blocks 0..4 are the walk cycle and block 5 the swing. Same again here -- the
census flags *candidates* (a short tail block, a bright spike) but only the
picture says which is which.

Output: tools/out/v211_blocks/<key>.png -- one row per block, 17 columns,
each row labelled b0..bN, 2x nearest-neighbour zoom.
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out\v211_blocks")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def frame_image(f, scale):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    src = f["px"]
    for y in range(f["h"]):
        base = y * f["w"]
        for x in range(f["w"]):
            v = src[base + x]
            if v != 255:
                px[x, y] = PAL[v] + (255,)
    if scale != 1:
        im = im.resize((f["w"] * scale, f["h"] * scale), Image.NEAREST)
    return im


WANT = [
    ("ultra",      "unit\\zerg\\ultra.grp",      1),
    ("guardian",   "unit\\zerg\\guardian.grp",   1),
    ("defiler",    "unit\\zerg\\defiler.grp",    1),
    ("queen",      "unit\\zerg\\queen.grp",      1),
    ("lurker",     "unit\\zerg\\lurknorm.grp",   1),
    ("lurker_bur", "unit\\zerg\\lurkburr.grp",   1),
    ("devourer",   "unit\\zerg\\devour.grp",     1),
    ("broodling",  "unit\\zerg\\brood.grp",      2),
    ("lurk_egg",   "unit\\zerg\\LurkEgg.grp",    1),
    ("medic",      "unit\\terran\\medic.grp",    2),
    ("valkyrie",   "unit\\terran\\bomber.grp",   1),
    ("spider",     "unit\\terran\\Spider.grp",   3),
]

os.makedirs(OUT, exist_ok=True)
for key, path, scale in WANT:
    r = load(path)
    if r is None:
        print("MISS", key, path)
        continue
    frames, mw, mh = r
    n = len(frames)
    blocks = (n + 16) // 17
    cw, ch = mw * scale, mh * scale
    lab = 34
    img = Image.new("RGBA", (lab + 17 * cw, blocks * ch), (22, 26, 34, 255))
    d = ImageDraw.Draw(img)
    for b in range(blocks):
        d.text((2, b * ch + ch // 2), "b%d" % b, fill=(240, 220, 120, 255))
        for dd in range(17):
            fi = b * 17 + dd
            if fi >= n:
                break
            im = frame_image(frames[fi], scale)
            img.paste(im, (lab + dd * cw, b * ch), im)
    img.save(os.path.join(OUT, key + ".png"))
    print("%-12s blocks=%-2d -> %s (%dx%d)"
          % (key, blocks, key + ".png", img.width, img.height))

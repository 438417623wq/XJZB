"""v2.11 batch B/C: compact per-block overview -- 4 sampled directions per
block instead of all 17.

The full 17-wide strips (probe_v211b.py) are the ground truth but they are
2210 px wide and expensive to eyeball twelve times over. This renders the same
information at a quarter of the size: directions 0/4/8/12 from every block,
stacked, so the block-by-block change (walk -> attack -> death) is visible at a
glance. When a unit looks ambiguous here, fall back to the full strip.

Output: tools/out/v211_blocks/<key>_ov.png
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


WANT = [
    ("ultra",      "unit\\zerg\\ultra.grp"),
    ("guardian",   "unit\\zerg\\guardian.grp"),
    ("defiler",    "unit\\zerg\\defiler.grp"),
    ("queen",      "unit\\zerg\\queen.grp"),
    ("lurker",     "unit\\zerg\\lurknorm.grp"),
    ("lurker_bur", "unit\\zerg\\lurkburr.grp"),
    ("devourer",   "unit\\zerg\\devour.grp"),
    ("broodling",  "unit\\zerg\\brood.grp"),
    ("lurk_egg",   "unit\\zerg\\LurkEgg.grp"),
    ("medic",      "unit\\terran\\medic.grp"),
    ("valkyrie",   "unit\\terran\\bomber.grp"),
    ("spider",     "unit\\terran\\Spider.grp"),
    # calibration rulers -- layouts already known from the shipped pipeline
    ("marine",     "unit\\terran\\marine.grp"),
    ("muta",       "unit\\zerg\\mutalid.grp"),
]

DIRS = [0, 4, 8, 12]

os.makedirs(OUT, exist_ok=True)
for key, path in WANT:
    r = load(path)
    if r is None:
        print("MISS", key, path)
        continue
    frames, mw, mh = r
    n = len(frames)
    blocks = (n + 16) // 17
    cw, ch = mw, mh
    lab = 30
    img = Image.new("RGBA", (lab + len(DIRS) * cw, blocks * ch), (22, 26, 34, 255))
    d = ImageDraw.Draw(img)
    for b in range(blocks):
        d.text((2, b * ch + ch // 2), "b%d" % b, fill=(240, 220, 120, 255))
        for k, dd in enumerate(DIRS):
            fi = b * 17 + dd
            if fi >= n:
                continue
            im = frame_image(frames[fi])
            img.paste(im, (lab + k * cw, b * ch), im)
    img.save(os.path.join(OUT, key + "_ov.png"))
    print("%-12s blocks=%-2d -> %s (%dx%d)"
          % (key, blocks, key + "_ov.png", img.width, img.height))

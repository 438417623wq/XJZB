"""v2.11: settle the three contested zerg building identities at large scale.

Two candidate assignments disagree, so this renders every frame of the files in
dispute, big enough to name by eye:
  * the CURRENT manifest says  pool=Snakey, sunken=SColony
  * the ImageTypes alignment says pool=chrysal, hydralisk den=Snakey,
    spore colony=SColony, sunken colony=Lurker
The sunken colony is the one with the long attack tentacle, the spore colony the
one with the squat spore sac, the spawning pool the one that is a shallow pool
of liquid, and the hydralisk den the mound with the round entrance hole.

Usage: python probe_v211an.py
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "v211_bld")
os.makedirs(OUT, exist_ok=True)

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

FILES = [
    ("fcolony.grp", "unit\\zerg\\fcolony.grp"),
    ("SColony.grp", "unit\\zerg\\SColony.grp"),
    ("Lurker.grp",  "unit\\zerg\\Lurker.grp"),
    ("Snakey.grp",  "unit\\zerg\\Snakey.grp"),
    ("chrysal.grp", "unit\\zerg\\chrysal.grp"),
    ("nest.grp",    "unit\\zerg\\nest.grp"),
    ("Mutapit.grp", "unit\\zerg\\Mutapit.grp"),
    ("MutaCham.grp", "unit\\zerg\\MutaCham.grp"),
    ("cerebrat.grp", "unit\\zerg\\cerebrat.grp"),
    ("RCluster.grp", "unit\\zerg\\RCluster.grp"),
    ("spire.grp",   "unit\\zerg\\spire.grp"),
    ("NydusPit.grp", "unit\\zerg\\NydusPit.grp"),
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
                px[x, y] = PAL[v] + (255,)
    return im


SCALE = 4
CELLW, CELLH = 640, 620
COLS = 3
rows = (len(FILES) + COLS - 1) // COLS
img = Image.new("RGBA", (COLS * CELLW, rows * CELLH), (16, 16, 22, 255))
dr = ImageDraw.Draw(img)
for k, (nm, path) in enumerate(FILES):
    r = load(path)
    cx = (k % COLS) * CELLW
    cy = (k // COLS) * CELLH
    if r is None:
        dr.text((cx + 6, cy + 6), "%s MISS" % nm, fill=(255, 90, 90, 255))
        continue
    frames, mw, mh = r
    dr.text((cx + 6, cy + 6), "%s  frames=%d %dx%d" % (nm, len(frames), mw, mh),
            fill=(255, 235, 140, 255))
    n = min(len(frames), 6)
    for j in range(n):
        f = frames[j]
        im = frame_image(f)
        im = im.resize((f["w"] * SCALE, f["h"] * SCALE), Image.NEAREST)
        ox = cx + (j % 3) * (CELLW // 3)
        oy = cy + 24 + (j // 3) * (CELLH // 2)
        img.paste(im, (ox, oy), im)
        dr.text((ox + 2, oy + 2), "f%d" % j, fill=(120, 255, 160, 255))

p = os.path.join(OUT, "contested.png")
img.save(p)
print("->", p)

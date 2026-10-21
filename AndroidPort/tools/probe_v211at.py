"""v2.11: read the walk-cycle length off the art, using verified units as rulers.

The manifest's walkRows must equal the number of frames in the walk cycle; if it
is too long the unit plays its own death frames while walking. Neither the
silhouette probes nor the numeric seam detectors (probe_v211as.py) can find that
boundary, so this renders direction 0 of every block at a size where the pose
change is visible, with the five ALREADY-VERIFIED units first as rulers:

    marine  walkRows=3   (blocks 0,1,2 walk; 3 attack; 12 death)
    zergling walkRows=3
    hydra   walkRows=2
    zealot  walkRows=5
    dragoon walkRows=8

Reading rule: the walk cycle ends at the first block whose pose is NOT a
plausible continuation of the locomotion loop -- for the rulers that is the
block that adds a muzzle flash / recoil.

Usage: python probe_v211at.py <part>
       part 1 = rulers + zerg units, part 2 = zerg buildings + terran BW
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
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "v211_unit")
os.makedirs(OUT, exist_ok=True)

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

RULERS = [
    ("marine   walk=3", "unit\\terran\\marine.grp"),
    ("zergling walk=3", "unit\\zerg\\zergling.grp"),
    ("hydra    walk=2", "unit\\zerg\\hydra.grp"),
    ("zealot   walk=5", "unit\\protoss\\zealot.grp"),
    ("dragoon  walk=8", "unit\\protoss\\dragoon.grp"),
]
ZERG = [
    ("ultra", "unit\\zerg\\ultra.grp"),
    ("queen", "unit\\zerg\\queen.grp"),
    ("defiler", "unit\\zerg\\defiler.grp"),
    ("guardian", "unit\\zerg\\guardian.grp"),
    ("devourer", "unit\\zerg\\devour.grp"),
    ("lurker", "unit\\zerg\\lurknorm.grp"),
    ("lurker_bur", "unit\\zerg\\lurkburr.grp"),
    ("broodling", "unit\\zerg\\brood.grp"),
    ("medic", "unit\\terran\\medic.grp"),
]

part = int(sys.argv[1]) if len(sys.argv) > 1 else 1
PATHS = RULERS + ZERG if part == 1 else ZERG

CELL = int(os.environ.get("CELL", "260"))


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


def tight(im):
    bb = im.getbbox()
    return im.crop(bb) if bb else im


rows = []
nb_max = 0
for key, path in PATHS:
    r = load(path)
    if r is None:
        print("MISS", key)
        continue
    frames, mw, mh = r
    nb = (len(frames) + 16) // 17
    nb_max = max(nb_max, nb)
    rows.append((key, frames, nb))
    print("%-18s frames=%-4d blocks=%-3d" % (key, len(frames), nb))

W = 120 + nb_max * CELL
H = len(rows) * CELL
img = Image.new("RGBA", (W, H), (16, 16, 22, 255))
dr = ImageDraw.Draw(img)
for row, (key, frames, nb) in enumerate(rows):
    y0 = row * CELL
    dr.text((4, y0 + 4), key, fill=(255, 235, 140, 255))
    for b in range(nb):
        fi = b * 17
        if fi >= len(frames):
            break
        im = tight(frame_image(frames[fi]))
        sc = min((CELL - 24) / max(1, im.width), (CELL - 24) / max(1, im.height))
        im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))),
                       Image.NEAREST)
        ox = 120 + b * CELL
        img.paste(im, (ox + (CELL - im.width) // 2,
                       y0 + 18 + (CELL - 18 - im.height) // 2), im)
        dr.text((ox + 4, y0 + 4), "b%d" % b, fill=(140, 220, 255, 255))

p = os.path.join(OUT, "walkread_%d.png" % part)
img.save(p)
print("->", p)

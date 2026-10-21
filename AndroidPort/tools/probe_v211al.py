"""v2.11: name every zerg building GRP by joining bwenums.h ImageTypes against
arr\\images.tbl, then render the result for visual confirmation.

Why this works when the four silhouette probes (v211q/r/t/z/aa) failed:
images.tbl is NOT sorted by GRP name, it is sorted by image id -- the same order
as the ImageTypes enum in bwenums.h. The repack interleaves extra `.lof/.lou/
.lod/.los` rows, so raw index != image id, but the GROUP SEQUENCE is identical.
The alignment is proven at the far end: after the Spore Colony group the table
continues Infest03 (Infested_Command_Center_Overlay), ZBuild
(Zerg_Construction_Large), ZBShad (Construction_Shadow), zSpawn01..03
(Spawn_Small/Medium/Large) -- exactly the enum order.

Usage: python probe_v211al.py
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

# image id -> GRP path. Derived, not guessed: the repack's images.tbl lists the
# non-LO rows in exactly the ImageTypes enum order, with six enum rows dropped
# (Overmind_Remnants, Zerg_Building_Morph, Zerg_Construction_Medium,
# Zerg_Construction_Small, Zerg_Building_Rubble_Small, ..._Large). Anchoring at
# both ends -- UCereb.grp==Cerebrate at the start, and
# ZBuild/ZBShad/zSpawn01-03 == Construction_Large/Construction_Shadow/
# Spawn_Small/Medium/Large at the end -- leaves zero free parameters.
MAP = [
    ("61 Cerebrate",          "unit\\zerg\\UCereb.grp"),
    ("130 Infested CC",       "unit\\terran\\control.grp"),
    ("131 Hatchery",          "unit\\zerg\\hatchery.grp"),
    ("132 Lair",              "unit\\zerg\\Lair.grp"),
    ("133 Hive",              "unit\\zerg\\Hive.grp"),
    ("134 Nydus Canal",       "unit\\zerg\\NydusPit.grp"),
    ("135 Hydralisk Den",     "unit\\zerg\\Snakey.grp"),
    ("136 Defiler Mound",     "unit\\zerg\\Mutapit.grp"),
    ("137 Greater Spire",     "unit\\zerg\\MutaCham.grp"),
    ("138 Queens Nest",       "unit\\zerg\\nest.grp"),
    ("139 Evolution Chamber", "unit\\zerg\\cerebrat.grp"),
    ("140 Ultralisk Cavern",  "unit\\zerg\\RCluster.grp"),
    ("141 Spire",             "unit\\zerg\\spire.grp"),
    ("142 Spawning Pool",     "unit\\zerg\\chrysal.grp"),
    ("143 Creep Colony",      "unit\\zerg\\fcolony.grp"),
    ("144 Spore Colony",      "unit\\zerg\\SColony.grp"),
    ("146 Sunken Colony",     "unit\\zerg\\Lurker.grp"),
    ("149 Extractor",         "unit\\zerg\\Extract.grp"),
    ("150 Mature Chrysalis",  "unit\\neutral\\kerrChry.grp"),
    ("147 Overmind shell",    "unit\\zerg\\Over1.grp"),
    ("148 Overmind bare",     "unit\\zerg\\Over2.grp"),
    ("- Infested overlay",    "unit\\zerg\\Infest03.grp"),
    ("- Zerg build morph",    "unit\\zerg\\ZBuild.grp"),
    # the two rows the CURRENT manifest gets wrong, shown for comparison
    ("OLD pool=Snakey",       "unit\\zerg\\Snakey.grp"),
    ("OLD sunken=SColony",    "unit\\zerg\\SColony.grp"),
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


SCALE = 2
CELLW, CELLH = 300, 300
COLS = 4
rows = (len(MAP) + COLS - 1) // COLS
img = Image.new("RGBA", (COLS * CELLW, rows * CELLH), (18, 18, 24, 255))
dr = ImageDraw.Draw(img)
for k, (name, path) in enumerate(MAP):
    r = load(path)
    cx = (k % COLS) * CELLW
    cy = (k // COLS) * CELLH
    if r is None:
        dr.text((cx + 6, cy + 6), "%s MISS %s" % (name, path), fill=(255, 90, 90, 255))
        print("MISS", name, path)
        continue
    frames, mw, mh = r
    # last frame = fully built pose for a building
    f = frames[-1]
    im = frame_image(f).resize((f["w"] * SCALE, f["h"] * SCALE), Image.NEAREST)
    img.paste(im, (cx + (CELLW - im.width) // 2,
                   cy + 22 + (CELLH - 22 - im.height) // 2), im)
    dr.text((cx + 6, cy + 6), "%s" % name, fill=(255, 235, 140, 255))
    dr.text((cx + 6, cy + 20), "%s f=%d %dx%d" % (os.path.basename(path), len(frames), mw, mh),
            fill=(150, 200, 255, 255))
    print("%-22s %-34s frames=%-3d cell=%dx%d" % (name, path, len(frames), mw, mh))

p = os.path.join(OUT, "zerg_map_proven.png")
img.save(p)
print("->", p)

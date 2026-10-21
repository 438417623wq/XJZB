"""v2.11 batch B/C: building identity sheets, big enough to actually name.

probe_v211l.py puts a whole race on one line at 2x, where a 128x192 evolution
chamber reads as a smudge and three purple spires look alike. This one takes an
explicit list, renders each first frame tight-cropped at 3x with its label, and
wraps 5 per row so the viewer cannot shrink it.

The point is to settle the identities the plan leaves open:
  * which GRP is the Hydralisk Den and which the Defiler Mound;
  * whether UCereb.grp really is the Ultralisk Cavern;
  * whether nest.grp really is the Queen's Nest.
spire.grp rides along as a control: it is already shipping and provably right,
so whatever renders identically to it belongs to the Spire line.

Usage: python probe_v211n.py [group]
  group = zerg1 (default) | zerg2 | terran2 | all
Output: tools/out/v211_bld/<group>_id.png
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out\v211_bld")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

GROUPS = {
    "zerg1": [
        ("Spire(control)", "unit\\zerg\\spire.grp"),
        ("Mutapit",        "unit\\zerg\\Mutapit.grp"),
        ("MutaCham",       "unit\\zerg\\MutaCham.grp"),
        ("nest",           "unit\\zerg\\nest.grp"),
        ("UCereb",         "unit\\zerg\\UCereb.grp"),
        ("cerebrat",       "unit\\zerg\\cerebrat.grp"),
        ("NydusPit",       "unit\\zerg\\NydusPit.grp"),
        ("Snakey",         "unit\\zerg\\Snakey.grp"),
        ("Extract",        "unit\\zerg\\Extract.grp"),
        ("ZBuild",         "unit\\zerg\\ZBuild.grp"),
    ],
    "zerg2": [
        ("fcolony",   "unit\\zerg\\fcolony.grp"),
        ("SColony",   "unit\\zerg\\SColony.grp"),
        ("RCluster",  "unit\\zerg\\RCluster.grp"),
        ("Over1",     "unit\\zerg\\Over1.grp"),
        ("Over2",     "unit\\zerg\\Over2.grp"),
        ("chrysal",   "unit\\zerg\\chrysal.grp"),
        ("hatchery",  "unit\\zerg\\hatchery.grp"),
        ("Lair",      "unit\\zerg\\Lair.grp"),
        ("Hive",      "unit\\zerg\\Hive.grp"),
        ("Infest03",  "unit\\zerg\\Infest03.grp"),
    ],
    # batch C: the two buildings that have no Type row yet, next to the rows
    # already in the game so the new ones can be told apart from them.
    "terran2": [
        ("EngBay 122",  "unit\\terran\\research.grp"),
        ("Armory 123",  "unit\\terran\\weaponpl.grp"),
        ("Science 116", "unit\\terran\\physics.grp"),
        ("Academy 112", "unit\\terran\\Academy.grp"),
        ("CovertOps",   "unit\\terran\\chemlab.grp"),
        ("PhysLab",     "unit\\terran\\GeneLab.grp"),
        ("MachineShp",  "unit\\terran\\machines.grp"),
        ("ComSat",      "unit\\terran\\ComSat.grp"),
        ("CtrlTower",   "unit\\terran\\controlT.grp"),
        ("NukeSilo",    "unit\\terran\\nukesilo.grp"),
        ("DryDocks",    "unit\\terran\\DryDocks.grp"),
        ("missileT",    "unit\\terran\\missileT.grp"),
    ],
}

SC = 3
PERROW = 5
GAP = 18


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


def tight(f):
    im = frame_image(f)
    bb = im.getbbox()
    return im.crop(bb) if bb else None


group = sys.argv[1] if len(sys.argv) > 1 else "zerg1"
items = GROUPS.get(group)
if items is None:
    print("unknown group", group, "expected", ",".join(GROUPS))
    sys.exit(1)

cells = []
for label, path in items:
    r = load(path)
    if r is None:
        print("MISS %-14s %s" % (label, path))
        cells.append((label, None))
        continue
    frames, mw, mh = r
    c = tight(frames[0])
    if c is None:
        print("EMPTY %-14s %s" % (label, path))
        cells.append((label, None))
        continue
    c = c.resize((c.width * SC, c.height * SC), Image.NEAREST)
    print("%-14s %-34s frames=%-3d cell=%dx%d tight=%dx%d"
          % (label, path, len(frames), mw, mh, c.width, c.height))
    cells.append((label, c))

cw = max((c.width for _, c in cells if c is not None), default=1) + GAP
ch = max((c.height for _, c in cells if c is not None), default=1) + GAP + 16
rows = (len(cells) + PERROW - 1) // PERROW
img = Image.new("RGBA", (PERROW * cw, rows * ch), (18, 22, 30, 255))
d = ImageDraw.Draw(img)
for i, (label, c) in enumerate(cells):
    x = (i % PERROW) * cw
    y = (i // PERROW) * ch
    d.text((x + 4, y + 2), label, fill=(240, 220, 120, 255))
    if c is not None:
        img.paste(c, (x + 4, y + 18), c)

name = "%s_id.png" % group
img.save(os.path.join(OUT, name))
print("-> %s (%dx%d)" % (name, img.width, img.height))

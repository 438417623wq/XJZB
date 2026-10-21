"""v2.11 batch B/C: one-line-per-building identity sheet.

probe_v211k.py writes one file per building, which costs an image read each.
Identity only needs the FIRST frame, so this packs every candidate building of
a race into a single row, labelled, at 2x. That answers "is this the building
the plan claims?" for a whole race in one look.

Usage: python probe_v211l.py <zerg|terran|protoss>
Output: tools/out/v211_bld/<race>_row.png
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

# (label, grp path) -- label names the units.dat building this SHOULD be, so a
# wrong render is visible as a mismatch between the label and the picture.
CAND = {
    "zerg": [
        ("134 Nydus",      "unit\\zerg\\NydusPit.grp"),
        ("135 HydraDen?",  "unit\\zerg\\Mutapit.grp"),
        ("136 DefilerM?",  "unit\\zerg\\Mutapit.grp"),
        ("137 GtSpire?",   "unit\\zerg\\spire.grp"),
        ("138 QueenNest",  "unit\\zerg\\nest.grp"),
        ("139 EvolCham?",  "unit\\zerg\\MutaCham.grp"),
        ("140 UltraCav?",  "unit\\zerg\\UCereb.grp"),
        ("141 Spire",      "unit\\zerg\\spire.grp"),
        ("143 CreepCol",   "unit\\zerg\\fcolony.grp"),
        ("144 SporeCol",   "unit\\zerg\\RCluster.grp"),
        ("146 SunkenCol",  "unit\\zerg\\SColony.grp"),
        ("147 Overmind",   "unit\\zerg\\Over1.grp"),
        ("149 Extractor",  "unit\\zerg\\Extract.grp"),
        ("151 Cerebrate",  "unit\\zerg\\cerebrat.grp"),
        ("150 Chrysalis",  "unit\\zerg\\chrysal.grp"),
        ("--- ZBuild",     "unit\\zerg\\ZBuild.grp"),
        ("131 Hatchery",   "unit\\zerg\\hatchery.grp"),
        ("132 Lair",       "unit\\zerg\\Lair.grp"),
        ("133 Hive",       "unit\\zerg\\Hive.grp"),
        ("142 Pool",       "unit\\zerg\\Snakey.grp"),
    ],
    "terran": [
        ("106 CC",         "unit\\terran\\control.grp"),
        ("107 Comsat",     "unit\\terran\\ComSat.grp"),
        ("108 NukeSilo",   "unit\\terran\\nukesilo.grp"),
        ("109 Depot",      "unit\\terran\\Depot.grp"),
        ("110 Refinery",   "unit\\terran\\refinery.grp"),
        ("111 Barracks",   "unit\\terran\\TBarrack.grp"),
        ("112 Academy",    "unit\\terran\\Academy.grp"),
        ("113 Factory",    "unit\\terran\\factory.grp"),
        ("114 Starport",   "unit\\terran\\starport.grp"),
        ("115 CtrlTower",  "unit\\terran\\controlT.grp"),
        ("116 ScienceFac", "unit\\terran\\physics.grp"),
        ("117 CovertOps",  "unit\\terran\\chemlab.grp"),
        ("118 PhysicsLab", "unit\\terran\\GeneLab.grp"),
        ("120 MachineShp", "unit\\terran\\machines.grp"),
        ("122 EngBay",     "unit\\terran\\research.grp"),
        ("123 Armory",     "unit\\terran\\weaponpl.grp"),
        ("124 Turret",     "unit\\terran\\missile.grp"),
        ("--- missilT",    "unit\\terran\\missileT.grp"),
        ("--- DryDocks",   "unit\\terran\\DryDocks.grp"),
        ("125 Bunker",     "unit\\terran\\PillBox.grp"),
    ],
    "protoss": [
        ("154 Nexus",      "unit\\protoss\\nexus.grp"),
        ("155 Robotic",    "unit\\protoss\\robotic.grp"),
        ("156 Pylon",      "unit\\protoss\\pylon.grp"),
        ("157 Assimil",    "unit\\protoss\\assim.grp"),
        ("160 Gateway",    "unit\\protoss\\gateway.grp"),
        ("162 Photon",     "unit\\protoss\\photon.grp"),
        ("163 Citadel",    "unit\\protoss\\citadel.grp"),
        ("164 CyberCore",  "unit\\protoss\\gencore.grp"),
        ("165 Archives",   "unit\\protoss\\archives.grp"),
        ("166 Forge",      "unit\\protoss\\forge.grp"),
        ("167 Stargate",   "unit\\protoss\\stargate.grp"),
        ("169 FleetBeacon","unit\\protoss\\beacon.grp"),
        ("170 Tribunal?",  "unit\\protoss\\warp.grp"),
        ("171 SupportBay?", "unit\\protoss\\prism.grp"),
        ("172 ShieldBat?", "unit\\protoss\\sbattery.grp"),
    ],
}


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


race = sys.argv[1] if len(sys.argv) > 1 else "zerg"
items = CAND[race]
SC = 2
cells = []
maxw = maxh = 1
for label, path in items:
    r = load(path)
    if r is None or len(r[0]) == 0:
        cells.append((label, None))
        continue
    frames, mw, mh = r
    im = frame_image(frames[0])
    bb = im.getbbox()
    im = im.crop(bb) if bb else im
    im = im.resize((im.width * SC, im.height * SC), Image.NEAREST)
    cells.append((label, im))
    maxw = max(maxw, im.width)
    maxh = max(maxh, im.height)

LAB = 130
cellw = maxw + 8
# 20 buildings in one 8000px line get downscaled to mush by the viewer, so wrap
# into blocks of 10 -- still one image read per race, but legible.
PERROW = 10
nrows = (len(cells) + PERROW - 1) // PERROW
img = Image.new("RGBA", (LAB + min(PERROW, len(cells)) * cellw,
                         nrows * (maxh + 40)), (18, 22, 30, 255))
d = ImageDraw.Draw(img)
for k, (label, im) in enumerate(cells):
    gx, gy = k % PERROW, k // PERROW
    x = LAB + gx * cellw
    y = gy * (maxh + 40)
    d.text((x + 2, y + 4), label, fill=(240, 220, 120, 255))
    if im is None:
        d.text((x + 2, y + 40), "MISS", fill=(255, 120, 120, 255))
        continue
    img.paste(im, (x + 2, y + 22), im)
d.text((2, 4), "%s\nfirst frame\n2x" % race, fill=(150, 200, 255, 255))
name = "%s_row.png" % race
img.save(os.path.join(OUT, name))
print("%s -> %s (%dx%d, %d items)" % (race, name, img.width, img.height, len(cells)))

"""v2.11 batch B: pick the building frame the command-card icon was drawn from.

The first overlay attempt compared the icon against frame 0 of each building and
the controls came out mediocre (hatchery 0.62, spire 0.58) while two pairings I
already trust scored highest (nest 0.84, NydusPit 0.87). The reason is that a
building GRP's early frames are construction stages; the icon shows the finished
building, which is a later frame. So: score the icon against EVERY frame and keep
the best, then report which frame won.

Control group first -- if the six shipping rows do not each win by a clear margin
over the wrong candidates, the whole idea is dead and the identity question has to
be answered some other way.

Usage: python probe_v211aa.py
Output: tools/out/v211_bld/frame_best.txt  +  frame_best.png
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\tools\out\v211_bld")
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

BOX = 48

# units.dat id -> label (from stat_txt.tbl, authoritative)
NAMES = {
    131: "Hatchery", 132: "Lair", 133: "Hive", 134: "NydusCanal",
    135: "HydraliskDen", 136: "DefilerMound", 137: "GreaterSpire",
    138: "QueensNest", 139: "EvolutionChamber", 140: "UltraliskCavern",
    141: "Spire", 142: "SpawningPool", 143: "CreepColony", 144: "SporeColony",
    146: "SunkenColony", 149: "Extractor", 150: "MatureCrysalis",
}

# every zerg building GRP we have, by short name
GRPS = {
    "hatchery": "unit\\zerg\\hatchery.grp",
    "Lair": "unit\\zerg\\Lair.grp",
    "Hive": "unit\\zerg\\Hive.grp",
    "NydusPit": "unit\\zerg\\NydusPit.grp",
    "UCereb": "unit\\zerg\\UCereb.grp",
    "Mutapit": "unit\\zerg\\Mutapit.grp",
    "MutaCham": "unit\\zerg\\MutaCham.grp",
    "nest": "unit\\zerg\\nest.grp",
    "spire": "unit\\zerg\\spire.grp",
    "Snakey": "unit\\zerg\\Snakey.grp",
    "fcolony": "unit\\zerg\\fcolony.grp",
    "RCluster": "unit\\zerg\\RCluster.grp",
    "SColony": "unit\\zerg\\SColony.grp",
    "Extract": "unit\\zerg\\Extract.grp",
    "cerebrat": "unit\\zerg\\cerebrat.grp",
    "chrysal": "unit\\zerg\\chrysal.grp",
}

# the six rows already shipping, as ground truth for the method
CONTROL = {131: "hatchery", 141: "spire", 142: "Snakey",
           143: "fcolony", 146: "SColony", 149: "Extract"}


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def alpha(f):
    w, h = f["w"], f["h"]
    im = Image.new("L", (w, h), 0)
    px = im.load()
    src = f["px"]
    for y in range(h):
        for x in range(w):
            if src[y * w + x] != 255:
                px[x, y] = 255
    bb = im.getbbox()
    return im.crop(bb) if bb else None


def fit(im, box):
    s = box / float(max(im.width, im.height))
    return im.resize((max(1, int(round(im.width * s))),
                      max(1, int(round(im.height * s)))), Image.NEAREST)


def iou(a, b, box=BOX):
    ca, cb = fit(a, box), fit(b, box)
    pa, pb = ca.load(), cb.load()
    oa = ((box - ca.width) // 2, (box - ca.height) // 2)
    ob = ((box - cb.width) // 2, (box - cb.height) // 2)
    both = union = 0
    for y in range(box):
        for x in range(box):
            va = 0 <= x - oa[0] < ca.width and 0 <= y - oa[1] < ca.height and pa[x - oa[0], y - oa[1]] > 127
            vb = 0 <= x - ob[0] < cb.width and 0 <= y - ob[1] < cb.height and pb[x - ob[0], y - ob[1]] > 127
            if va or vb:
                union += 1
                if va and vb:
                    both += 1
    return both / float(union) if union else 0.0


icons = load("unit\\cmdbtns\\cmdicons.grp")[0]
masks = {}
for short, path in GRPS.items():
    r = load(path)
    if r is None:
        print("MISS %s" % path)
        continue
    ms = [alpha(f) for f in r[0]]
    masks[short] = [m for m in ms if m is not None]
    print("%-10s %d frames, %d non-empty" % (short, len(ms), len(masks[short])))

lines = []
print("\n%-16s %-12s %-6s %-8s %s" % ("id/label", "best grp", "score", "frame", "runner-up"))
report = []
for idx in sorted(NAMES):
    im = alpha(icons[idx])
    if im is None:
        continue
    scored = []
    for short, ms in masks.items():
        best, bf = -1.0, -1
        for fi, m in enumerate(ms):
            v = iou(im, m)
            if v > best:
                best, bf = v, fi
        scored.append((best, short, bf))
    scored.sort(reverse=True)
    top, second = scored[0], scored[1]
    flag = ""
    if idx in CONTROL:
        flag = "  <-- CONTROL, expect %s" % CONTROL[idx]
    line = "%-16s %-12s %.3f  f%-4d  %s %.3f%s" % (
        "%d %s" % (idx, NAMES[idx]), top[1], top[0], top[2], second[1], second[0], flag)
    print(line)
    lines.append(line)
    report.append((idx, top[1], top[0], top[2], second[1], second[0]))

with open(os.path.join(OUT, "frame_best.txt"), "w") as fh:
    fh.write("\n".join(lines))

# visual: icon vs its best frame vs the runner-up, all three side by side
CELL = 96
img = Image.new("RGB", (CELL * 3 + 24, (CELL + 26) * len(report)), (16, 18, 24))
d = ImageDraw.Draw(img)
for row, (idx, g1, s1, f1, g2, s2) in enumerate(report):
    y = row * (CELL + 26)
    d.text((4, y + 4), "%d %s" % (idx, NAMES[idx]), fill=(240, 220, 120))
    ic = fit(alpha(icons[idx]), CELL)
    img.paste(ic.convert("RGB"), (4, y + 20))
    for col, (g, fi) in enumerate(((g1, f1), (g2, -1))):
        m = masks[g][fi] if fi >= 0 else masks[g][len(masks[g]) // 2]
        t = fit(m, CELL).convert("RGB")
        img.paste(t, (4 + (col + 1) * (CELL + 4), y + 20))
img.save(os.path.join(OUT, "frame_best.png"))
print("\n-> frame_best.txt / frame_best.png")
PT.close()
SD.close()
BD.close()

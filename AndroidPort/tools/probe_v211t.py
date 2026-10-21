"""v2.11 batch B: settle every zerg building identity numerically.

stat_txt.tbl (read by probe_v211s.py) gives the names: 135 Hydralisk Den,
136 Defiler Mound, 137 Greater Spire, 138 Queen's Nest, 139 Evolution Chamber,
140 Ultralisk Cavern, 141 Spire, 142 Spawning Pool, 143 Creep Colony,
144 Spore Colony, 146 Sunken Colony. cmdicons.grp is indexed by the same
units.dat id, so icon 135 IS the Hydralisk Den's own wireframe.

What is still unknown is which GRP file draws which of those. The archives name
the zerg building art after nothing useful (Mutapit, MutaCham, UCereb,
cerebrat), and naming them by eye failed: at icon size every wireframe is a
purple smudge.

So match them by shape instead. The command-card wireframe is a silhouette of
the same sprite, so normalising both alpha masks to a common box and taking the
IoU of the two should peak on the true pairing. Six pairs are already shipping
and provably right (hatchery 131, Spire 141, Pool 142, Creep 143, Sunken 146,
Extractor 149); they run first as the control. If the control does not peak, the
method is invalid and nothing after it means anything.

Usage: python probe_v211t.py
Output: stdout matrix + tools/out/v211_bld/iou_matrix.txt
"""
import os
import sys

from PIL import Image

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

# (units.dat id, name, the grp we already believe, or None)
ICONS = [
    (131, "Hatchery",       "unit\\zerg\\hatchery.grp"),
    (141, "Spire",          "unit\\zerg\\spire.grp"),
    (142, "SpawningPool",   "unit\\zerg\\Snakey.grp"),
    (143, "CreepColony",    "unit\\zerg\\fcolony.grp"),
    (146, "SunkenColony",   "unit\\zerg\\SColony.grp"),
    (149, "Extractor",      "unit\\zerg\\Extract.grp"),
    (132, "Lair",           None),
    (133, "Hive",           None),
    (134, "NydusCanal",     None),
    (135, "HydraliskDen",   None),
    (136, "DefilerMound",   None),
    (137, "GreaterSpire",   None),
    (138, "QueensNest",     None),
    (139, "EvolutionChamber", None),
    (140, "UltraliskCavern", None),
    (144, "SporeColony",    None),
    (147, "Overmind",       None),
    (150, "MatureCrysalis", None),
    (151, "Cerebrate",      None),
]

# every zerg building grp that exists, including the ones named cryptically
GRPS = [
    "unit\\zerg\\hatchery.grp",
    "unit\\zerg\\Lair.grp",
    "unit\\zerg\\Hive.grp",
    "unit\\zerg\\Snakey.grp",
    "unit\\zerg\\Extract.grp",
    "unit\\zerg\\spire.grp",
    "unit\\zerg\\SColony.grp",
    "unit\\zerg\\fcolony.grp",
    "unit\\zerg\\RCluster.grp",
    "unit\\zerg\\Mutapit.grp",
    "unit\\zerg\\MutaCham.grp",
    "unit\\zerg\\nest.grp",
    "unit\\zerg\\UCereb.grp",
    "unit\\zerg\\NydusPit.grp",
    "unit\\zerg\\cerebrat.grp",
    "unit\\zerg\\ZBuild.grp",
    "unit\\zerg\\chrysal.grp",
    "unit\\zerg\\Over1.grp",
    "unit\\zerg\\Over2.grp",
    "unit\\zerg\\Infest03.grp",
]

BOX = 96


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def mask_of(f):
    """Alpha mask of one GRP frame, cropped to its bounding box."""
    w, h = f["w"], f["h"]
    im = Image.new("L", (w, h), 0)
    px = im.load()
    src = f["px"]
    for y in range(h):
        base = y * w
        for x in range(w):
            if src[base + x] != 255:
                px[x, y] = 255
    bb = im.getbbox()
    return im.crop(bb) if bb else None


def norm(im, box=BOX):
    """Scale into `box` on the longer side, centred, keeping the aspect ratio."""
    if im is None:
        return None
    s = box / float(max(im.width, im.height))
    w = max(1, int(round(im.width * s)))
    h = max(1, int(round(im.height * s)))
    im = im.resize((w, h), Image.NEAREST)
    out = Image.new("L", (box, box), 0)
    out.paste(im, ((box - w) // 2, (box - h) // 2))
    return out


def iou(a, b):
    if a is None or b is None:
        return -1.0
    pa, pb = a.load(), b.load()
    inter = union = 0
    for y in range(BOX):
        for x in range(BOX):
            va = pa[x, y] > 127
            vb = pb[x, y] > 127
            if va or vb:
                union += 1
                if va and vb:
                    inter += 1
    return inter / float(union) if union else -1.0


data, gaps = SD.read_with_gaps("unit\\cmdbtns\\cmdicons.grp")
iframes, imw, imh = grpm.decode_grp(data, gaps)
print("cmdicons %d frames %dx%d" % (len(iframes), imw, imh))

masks = {}
for path in GRPS:
    r = load(path)
    if r is None:
        print("MISS grp", path)
        continue
    frames = r[0]
    m = norm(mask_of(frames[0]))
    if m is None:
        print("EMPTY grp", path)
        continue
    masks[path] = m
print("masks: %d" % len(masks))

lines = []
lines.append("icon id  name                best matches (iou)")
for idx, name, known in ICONS:
    if idx >= len(iframes):
        print("icon miss", idx)
        continue
    ic = norm(mask_of(iframes[idx]))
    scored = sorted(((iou(ic, m), p) for p, m in masks.items()), reverse=True)
    top = scored[:4]
    tag = ""
    if known is not None:
        rank = [p for _, p in scored].index(known) + 1 if known in masks else -1
        tag = "  [known=%s rank=%d iou=%.3f]" % (
            os.path.basename(known), rank,
            dict((p, s) for s, p in scored).get(known, -1.0))
    print("%3d %-18s %s%s" % (idx, name,
                              "  ".join("%.3f %s" % (s, os.path.basename(p)) for s, p in top), tag))
    lines.append("%3d %-18s %s%s" % (idx, name,
                 "  ".join("%.3f %s" % (s, os.path.basename(p)) for s, p in top), tag))

with open(os.path.join(OUT, "iou_matrix.txt"), "w", encoding="utf8") as fp:
    fp.write("\n".join(lines) + "\n")
print("-> iou_matrix.txt")

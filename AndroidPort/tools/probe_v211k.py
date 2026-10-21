"""v2.11 batch B/C: contact sheet for the new building GRPs.

Buildings are single-pose sheets (kind 1 in the manifest: `frames` animation
frames laid out `cols` per row), so the decision here is different from a unit:
there is no walk/attack seam to find, only
  (a) does the GRP hold the building the plan claims it does, and
  (b) how many animation frames does it have (the manifest's `maxf` cap).

Both are answered by rendering every frame of the file at 2x in one strip.

The zerg rows are the ones that actually need eyes: the plan itself flags
`evolcham` and `mutapit` with question marks, and v2.8 shipped the creep colony
as the sunken colony, so a wrong path silently renders the wrong building.

Usage: python probe_v211k.py [group]
  groups: zerg (default), terran, protoss, all
Output: tools/out/v211_bld/<key>.png
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
    # the zerg structures batch B adds, plus the ones whose identity the plan
    # itself questions. Paths are copied from pipeline_expand.py BUILDINGS.
    "zerg": {
        "creep":     "unit\\zerg\\fcolony.grp",     # creep colony (id 143)
        "sunken":    "unit\\zerg\\SColony.grp",     # sunken colony (id 146)
        "spore":     "unit\\zerg\\RCluster.grp",    # spore colony (id 144)
        "evolcham":  "unit\\zerg\\MutaCham.grp",    # evolution chamber? (139)
        "mutapit":   "unit\\zerg\\Mutapit.grp",     # hydralisk den / defiler mound?
        "nest":      "unit\\zerg\\nest.grp",        # queen's nest (138)
        "nydus":     "unit\\zerg\\NydusPit.grp",    # nydus canal (134)
        "spire":     "unit\\zerg\\spire.grp",       # greater spire base
        "pool":      "unit\\zerg\\Snakey.grp",
        "hatchery":  "unit\\zerg\\hatchery.grp",
    },
    "terran": {
        "engbay":     "unit\\terran\\research.grp",   # engineering bay (122)
        "armory":     "unit\\terran\\weaponpl.grp",   # armory (123)
        "sciencefac": "unit\\terran\\physics.grp",    # science facility (116)
        "comsat":     "unit\\terran\\ComSat.grp",
        "controlt":   "unit\\terran\\controlT.grp",
        "covertops":  "unit\\terran\\chemlab.grp",
        "physlab":    "unit\\terran\\GeneLab.grp",
        "machineshop": "unit\\terran\\machines.grp",
        "nukesilo":   "unit\\terran\\nukesilo.grp",
        "drydocks":   "unit\\terran\\DryDocks.grp",
        "turret2":    "unit\\terran\\missileT.grp",
        "turret":     "unit\\terran\\missile.grp",
    },
    "protoss": {
        "tribunal":   "unit\\protoss\\warp.grp",      # arbiter tribunal? (170)
        "supportbay": "unit\\protoss\\prism.grp",     # robotics support bay? (171)
        "sbattery":   "unit\\protoss\\sbattery.grp",  # decodes to 0 frames?
    },
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


group = sys.argv[1] if len(sys.argv) > 1 else "zerg"
want = GROUPS.keys() if group == "all" else [group]
os.makedirs(OUT, exist_ok=True)

for g in want:
    for key, path in GROUPS[g].items():
        r = load(path)
        if r is None:
            print("%-12s MISS  %s" % (key, path))
            continue
        frames, mw, mh = r
        n = len(frames)
        if n == 0:
            print("%-12s ZERO FRAMES  %s" % (key, path))
            continue
        show = min(n, 24)
        SC = 2
        cw, ch = mw * SC, mh * SC
        COLS = min(show, 12)
        rows = (show + COLS - 1) // COLS
        img = Image.new("RGBA", (COLS * cw, rows * (ch + 16)),
                        (18, 22, 30, 255))
        d = ImageDraw.Draw(img)
        for k in range(show):
            f = frames[k]
            im = frame_image(f)
            im = im.resize((mw * SC, mh * SC), Image.NEAREST)
            gx, gy = k % COLS, k // COLS
            x, y = gx * cw, gy * (ch + 16)
            d.text((x + 2, y), "f%d" % k, fill=(240, 220, 120, 255))
            img.paste(im, (x, y + 14), im)
        img.save(os.path.join(OUT, "%s.png" % key))
        print("%-12s n=%-4d cell=%dx%d -> %s.png (%dx%d)"
              % (key, n, mw, mh, key, img.width, img.height))

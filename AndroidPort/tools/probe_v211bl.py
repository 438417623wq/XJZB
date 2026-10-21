"""v2.11: per-block flash/brightness detector.

Complements probe_v211p.py (the red death detector).  Attack animations in the
original GRPs are marked by a bright graphic - a muzzle flash, a psionic glow or
a blade motion streak - which the death animations do not have.  Measuring the
fraction of very bright pixels per 17-frame block therefore locates the attack
block even when the silhouette is ambiguous.

Prints, per block: frames, pixel count, red%, bright% (lum > 190) and mean lum.

Usage: python probe_v211bl.py <key> [key ...]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

PATHS = {
    "marine": "unit\\terran\\marine.grp",
    "scv": "unit\\terran\\SCV.grp",
    "zergling": "unit\\zerg\\zergling.grp",
    "hydra": "unit\\zerg\\hydra.grp",
    "zealot": "unit\\protoss\\zealot.grp",
    "dragoon": "unit\\protoss\\dragoon.grp",
    "ultra": "unit\\zerg\\ultra.grp",
    "queen": "unit\\zerg\\queen.grp",
    "defiler": "unit\\zerg\\defiler.grp",
    "guardian": "unit\\zerg\\guardian.grp",
    "devourer": "unit\\zerg\\devour.grp",
    "lurker": "unit\\zerg\\lurknorm.grp",
    "lurker_bur": "unit\\zerg\\lurkburr.grp",
    "broodling": "unit\\zerg\\brood.grp",
    "medic": "unit\\terran\\medic.grp",
    "valkyrie": "unit\\terran\\bomber.grp",
    "spider": "unit\\terran\\Spider.grp",
    "lurk_egg": "unit\\zerg\\LurkEgg.grp",
    "lurker_sd": "unit\\zerg\\Lurker.grp",
}


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


for key in sys.argv[1:]:
    res = load(PATHS[key])
    if res is None:
        print("MISS", key)
        continue
    frames, mw, mh = res
    nb = (len(frames) + 16) // 17
    print("=== %s  frames=%d blocks=%d cell=%dx%d" % (key, len(frames), nb, mw, mh))
    for b in range(nb):
        nfr = min(17, len(frames) - b * 17)
        npx = red = bright = lumsum = 0
        for k in range(b * 17, b * 17 + nfr):
            f = frames[k]
            for v in f["px"]:
                if v == 255:
                    continue
                r, g, bl = PAL[v]
                lum = (r * 299 + g * 587 + bl * 114) // 1000
                npx += 1
                lumsum += lum
                if lum > 190:
                    bright += 1
                if r > 90 and r > 1.7 * g + 12 and r > 1.7 * bl + 12:
                    red += 1
        if npx == 0:
            print("  b%-3d n=%-3d EMPTY" % (b, nfr))
            continue
        print("  b%-3d n=%-3d px=%-7d red=%5.1f%% bright=%5.1f%% lum=%5.1f"
              % (b, nfr, npx, 100.0 * red / npx, 100.0 * bright / npx,
                 lumsum / float(npx)))

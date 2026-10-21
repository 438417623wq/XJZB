"""v2.11: locate the DEATH segment of a unit GRP numerically.

Red gore is the one thing in this art set that cannot be confused with a walk
or an attack pose, so it is the one boundary a number can find reliably. For
every block this prints the share of pixels whose palette colour is strongly
red-dominant, plus mean luma. The first block with a big red share starts the
death run; everything before it is walk/attack and gets decided by eye.

This exists because the walk/attack seam is NOT numerically detectable (tried
in probe_v211h/m: even manifest-proven layouts show ~10% pixel churn between
any two blocks), while the death seam is trivial.

Usage: python probe_v211p.py <key> [key...]
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
RED = [(r > 90 and r > 1.7 * g + 12 and r > 1.7 * b + 12)
       for (r, g, b) in PAL]
LUM = [0.30 * r + 0.59 * g + 0.11 * b for (r, g, b) in PAL]

PATHS = {
    "ultra": "unit\\zerg\\ultra.grp",
    "queen": "unit\\zerg\\queen.grp",
    "defiler": "unit\\zerg\\defiler.grp",
    "guardian": "unit\\zerg\\guardian.grp",
    "devourer": "unit\\zerg\\devour.grp",
    "lurker": "unit\\zerg\\lurknorm.grp",
    "lurker_bur": "unit\\zerg\\lurkburr.grp",
    "broodling": "unit\\zerg\\brood.grp",
    "lurk_egg": "unit\\zerg\\LurkEgg.grp",
    "medic": "unit\\terran\\medic.grp",
    "valkyrie": "unit\\terran\\bomber.grp",
    "spider": "unit\\terran\\Spider.grp",
    "scv": "unit\\terran\\scv.grp",
    "marine": "unit\\terran\\marine.grp",
    "zergling": "unit\\zerg\\zergling.grp",
    "hydra": "unit\\zerg\\hydra.grp",
    "muta": "unit\\zerg\\mutalid.grp",
    "zealot": "unit\\protoss\\zealot.grp",
    "dragoon": "unit\\protoss\\dragoon.grp",
    "templar": "unit\\protoss\\templar.grp",
}


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


for key in sys.argv[1:]:
    r = load(PATHS[key])
    if r is None:
        print("MISS", key)
        continue
    frames, mw, mh = r
    n = len(frames)
    nb = (n + 16) // 17
    print("=== %s frames=%d blocks=%d cell=%dx%d" % (key, n, nb, mw, mh))
    for b in range(nb):
        npx = red = 0
        lum = 0.0
        cnt = min(17, n - b * 17)
        for d in range(cnt):
            f = frames[b * 17 + d]
            src = f["px"]
            for v in src:
                if v == 255:
                    continue
                npx += 1
                lum += LUM[v]
                if RED[v]:
                    red += 1
        print("   b%-3d frames=%-3d px=%-7d red=%.1f%%  lum=%.1f"
              % (b, cnt, npx, 100.0 * red / max(1, npx),
                 lum / max(1, npx)))

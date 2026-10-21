"""v2.11: block-to-block nearest-neighbour chain.

All earlier numeric attempts asked "where is the seam?" and failed because a
walk cycle has no seam - it is a closed loop.  This asks the right question:
"which earlier block does this block look most like?"

In a walk cycle of length W every block b is (nearly) identical to b-W, so the
chain reads  b -> b-W  for every b in the walk run.  Once the walk ends the
chain breaks (attack / death blocks have no earlier twin, or match the walk
start).

Distance is computed on a single direction (default 0) over the raw palette
RGB, ignoring transparent pixels, so it is independent of the crop box.

Usage: python probe_v211bo.py <key> [key ...]
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
    "firebat": "unit\\terran\\firebat.grp",
    "zergling": "unit\\zerg\\zergling.grp",
    "hydra": "unit\\zerg\\hydra.grp",
    "drone": "unit\\zerg\\drone.grp",
    "muta": "unit\\zerg\\mutalid.grp",
    "over": "unit\\zerg\\overlord.grp",
    "zealot": "unit\\protoss\\zealot.grp",
    "dragoon": "unit\\protoss\\dragoon.grp",
    "templar": "unit\\protoss\\templar.grp",
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

DIR = int(os.environ.get("DIR", "0"))


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def flat(f):
    """Return (w, h, list of rgb or None) for one frame."""
    w, h, px = f["w"], f["h"], f["px"]
    out = []
    for v in px:
        out.append(None if v == 255 else PAL[v])
    return w, h, out


def fdist(a, b):
    wa, ha, pa = a
    wb, hb, pb = b
    if wa != wb or ha != hb:
        # pad the smaller into the top-left of the larger
        w = max(wa, wb)
        h = max(ha, hb)

        def pad(ww, hh, pp):
            q = [None] * (w * h)
            for y in range(hh):
                for x in range(ww):
                    q[y * w + x] = pp[y * ww + x]
            return q
        pa = pad(wa, ha, pa)
        pb = pad(wb, hb, pb)
        wa = wb = w
        ha = hb = h
    tot = 0
    n = 0
    for ca, cb in zip(pa, pb):
        if ca is None and cb is None:
            continue
        if ca is None or cb is None:
            tot += 200
            n += 1
            continue
        tot += (abs(ca[0] - cb[0]) + abs(ca[1] - cb[1]) + abs(ca[2] - cb[2])) / 3.0
        n += 1
    return (tot / n) if n else 0.0


for key in sys.argv[1:]:
    res = load(PATHS[key])
    if res is None:
        print("MISS", key)
        continue
    frames, mw, mh = res
    nb = (len(frames) + 16) // 17
    fl = []
    for b in range(nb):
        k = b * 17 + DIR
        fl.append(flat(frames[k]) if k < len(frames) else None)
    print("=== %s  frames=%d blocks=%d dir=%d" % (key, len(frames), nb, DIR))
    print("   b -> best earlier match (dist)   [d(b,b-1) for scale]")
    for b in range(nb):
        if fl[b] is None:
            print("   b%-3d <no frame>" % b)
            continue
        bestj, bestd = -1, 1e9
        for j in range(b):
            if fl[j] is None:
                continue
            d = fdist(fl[b], fl[j])
            if d < bestd:
                bestd, bestj = d, j
        prev = fdist(fl[b], fl[b - 1]) if b > 0 else 0.0
        lag = (b - bestj) if bestj >= 0 else 0
        print("   b%-3d -> b%-3d (d=%6.1f, lag=%2d)   d(b,b-1)=%6.1f"
              % (b, bestj, bestd, lag, prev))

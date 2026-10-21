"""v2.11: walk-period detector - the one numeric method that should work.

Every earlier numeric attempt (probe_v211as/az/bd/bg) compared ADJACENT blocks
and failed.  The reason is that a walk cycle is not marked by any local feature;
it is marked by PERIODICITY.  If the walk cycle is W blocks long, then for every
block b >= W inside the walk run, block b is (nearly) identical to block b-W.

So: for each candidate W, measure how far the sequence stays periodic:

    d(b, W) = distance(block b, block b - W)
    run(W)  = length of the longest run of consecutive b (starting at b >= W)
              with d(b, W) < T

The true walk length shows a long periodic run; a wrong W does not, because the
animation only repeats at its real period.

Also prints, for reference, the red/bright signature of the block that starts
right after the detected run (the attack block usually follows the walk).

Usage: python probe_v211bn.py <key> [key ...]
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
    "over": "unit\\zerg\\overlord.grp",
    "muta": "unit\\zerg\\mutalid.grp",
    "drone": "unit\\zerg\\drone.grp",
}

# directions sampled for the signature (0 = down, 4 = left/side)
DIRS = (0, 4, 8)


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def block_sig(frames, b, mw, mh):
    """Flatten one 17-frame block (all directions) into an index list."""
    out = []
    for d in range(17):
        k = b * 17 + d
        if k >= len(frames):
            out.append(None)
            continue
        f = frames[k]
        out.append((f["x"], f["y"], f["w"], f["h"], f["px"]))
    return out


def dist(sa, sb):
    """Mean per-pixel colour distance between two block signatures."""
    tot = 0
    n = 0
    for fa, fb in zip(sa, sb):
        if fa is None or fb is None:
            continue
        if fa[2] != fb[2] or fa[3] != fb[3]:
            # different cell shape: compare only the overlapping part
            pass
        wa, ha, pa = fa[2], fa[3], fa[4]
        wb, hb, pb = fb[2], fb[3], fb[4]
        w = min(wa, wb)
        h = min(ha, hb)
        for y in range(h):
            ra = y * wa
            rb = y * wb
            for x in range(w):
                va = pa[ra + x]
                vb = pb[rb + x]
                if va == 255 and vb == 255:
                    continue
                if va == 255 or vb == 255:
                    tot += 255
                    n += 1
                    continue
                ca = PAL[va]
                cb = PAL[vb]
                tot += (abs(ca[0] - cb[0]) + abs(ca[1] - cb[1])
                        + abs(ca[2] - cb[2])) // 3
                n += 1
    return (tot / float(n)) if n else 0.0


for key in sys.argv[1:]:
    res = load(PATHS[key])
    if res is None:
        print("MISS", key)
        continue
    frames, mw, mh = res
    nb = (len(frames) + 16) // 17
    sigs = [block_sig(frames, b, mw, mh) for b in range(nb)]
    print("=== %s  frames=%d blocks=%d cell=%dx%d" % (key, len(frames), nb, mw, mh))
    adj = [dist(sigs[b], sigs[b - 1]) for b in range(1, nb)]
    med = sorted(adj)[len(adj) // 2] if adj else 1.0
    T = max(4.0, 0.45 * med)
    print("   adjacent dist median=%.1f  -> threshold T=%.1f" % (med, T))
    print("   W   run  firstrun  mean(dist to b-W)")
    best = []
    for W in range(1, nb):
        ds = [dist(sigs[b], sigs[b - W]) for b in range(W, nb)]
        run = 0
        bestrun = 0
        start = -1
        cur = -1
        for i, dv in enumerate(ds):
            if dv < T:
                if cur < 0:
                    cur = i
                run += 1
                if run > bestrun:
                    bestrun = run
                    start = cur
            else:
                run = 0
                cur = -1
        mean = sum(ds) / float(len(ds)) if ds else 0.0
        print("   %-3d %-4d %-9d %.1f" % (W, bestrun, W + start if start >= 0 else -1, mean))
        best.append((bestrun, -mean, W))
    best.sort(reverse=True)
    print("   -> top3 by run: %s" % ([(w, r) for r, m, w in best[:3]],))

"""Histogram the palette indices used by effect GRPs vs unit GRPs.

Team recolouring rewrites indices 8..15. That is right for units/buildings but
wrong for effects: a muzzle flash that happens to use index 8-15 would turn
blue. This checks which indices the effect sheets actually reference.
"""
import os
import collections
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


for label, path in [("tmeFlshS", r"unit\thingy\tmeFlshS.grp"),
                    ("tmeFlshL", r"unit\thingy\tmeFlshL.grp"),
                    ("bsmoke", r"unit\thingy\bsmoke.grp"),
                    ("ephFire", r"unit\bullet\ephFire.grp"),
                    ("tBangS", r"unit\thingy\tBangS.grp"),
                    ("marine", r"unit\terran\marine.grp")]:
    r = load(path)
    if r is None:
        print(label, "MISS")
        continue
    frames, mw, mh = r
    hist = collections.Counter()
    for f in frames:
        for v in f["px"]:
            if v != 255:
                hist[v] += 1
    team_use = sum(c for v, c in hist.items() if 8 <= v <= 15)
    total = sum(hist.values())
    top = sorted(hist.items(), key=lambda kv: -kv[1])[:10]
    print("%-9s frames=%3d  px=%7d  team(8-15)=%d (%.1f%%)" %
          (label, len(frames), total, team_use, 100.0 * team_use / max(1, total)))
    print("           top indices:", top)

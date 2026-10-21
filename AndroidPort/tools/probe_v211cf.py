"""v2.11 batch B/C: locate the effect + BW-unit GRPs and report frame counts.

Usage: python probe_v211cf.py [group]
Groups: effects, deaths, bwunits, all
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

EFFECTS = [
    "unit\\thingy\\Dswarm.grp",
    "unit\\thingy\\dswarm.grp",
    "unit\\thingy\\ensGooS.grp",
    "unit\\thingy\\ehaMed.grp",
    "unit\\thingy\\disrupt.grp",
    "unit\\thingy\\MaelHit.grp",
    "unit\\thingy\\psiStorm.grp",
    "unit\\thingy\\ensGooM.grp",
    "unit\\thingy\\ensGooL.grp",
    "unit\\thingy\\spooge.grp",
    "unit\\thingy\\nukehit.grp",
    "unit\\thingy\\nukebeam.grp",
    "unit\\bullet\\grenade.grp",
    "unit\\bullet\\pspark.grp",
    "unit\\thingy\\DWeb.grp",
    "unit\\thingy\\dweb.grp",
]

DEATHS = [
    "unit\\zerg\\ultra.grp",
    "unit\\zerg\\queen.grp",
    "unit\\zerg\\defiler.grp",
    "unit\\zerg\\lurknorm.grp",
    "unit\\zerg\\lurkburr.grp",
    "unit\\terran\\medic.grp",
    "unit\\zerg\\guardian.grp",
    "unit\\zerg\\devour.grp",
    "unit\\zerg\\brood.grp",
    "unit\\zerg\\LurkEgg.grp",
]

BWUNITS = [
    "unit\\terran\\medic.grp",
    "unit\\terran\\bomber.grp",
    "unit\\terran\\Spider.grp",
    "unit\\terran\\valkyrie.grp",
    "unit\\zerg\\ultra.grp",
    "unit\\zerg\\queen.grp",
    "unit\\zerg\\defiler.grp",
    "unit\\zerg\\guardian.grp",
    "unit\\zerg\\devour.grp",
    "unit\\zerg\\lurknorm.grp",
    "unit\\zerg\\lurkburr.grp",
    "unit\\zerg\\brood.grp",
    "unit\\zerg\\LurkEgg.grp",
    "unit\\zerg\\Scourge.grp",
]

GROUPS = {"effects": EFFECTS, "deaths": DEATHS, "bwunits": BWUNITS}
if len(sys.argv) > 1 and sys.argv[1] != "all":
    todo = [(sys.argv[1], GROUPS[sys.argv[1]])]
else:
    todo = list(GROUPS.items())

for name, paths in todo:
    print("=== %s ===" % name)
    for p in paths:
        hit = None
        for tag, ar in (("PT", PT), ("SD", SD), ("BD", BD)):
            if ar.has(p):
                data, gaps = ar.read_with_gaps(p)
                r = grpm.decode_grp(data, gaps)
                if r is None:
                    hit = (tag, "decode-fail", 0)
                else:
                    frames, mw, mh = r
                    hit = (tag, "%d frames %dx%d" % (len(frames), mw, mh),
                           (len(frames) + 16) // 17)
                break
        if hit is None:
            print("  MISS %-34s" % p)
        else:
            print("  %-4s %-34s %-22s blocks=%d" % (hit[0], p, hit[1], hit[2]))

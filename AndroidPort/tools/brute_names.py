"""Brute-force candidate GRP names for the assets not found via images.tbl."""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
BD = sc_archive.Archive(r"F:\KF\XJZB\BrooDat.mpq")
PT = sc_archive.Archive(r"F:\KF\XJZB\patch_rt.mpq")


def probe(name):
    for tag, ar in (("SD", SD), ("BD", BD), ("PT", PT)):
        if ar.has(name):
            return tag
    return None


dirs = ["unit\\neutral", "unit\\thingy", "unit\\terran", "unit\\zerg", "unit\\cmdbtns",
        "thingy\\neutral", "unit\\tileset\\jungle"]
cands = ["mineral field.grp", "mineral field 1.grp", "mineral field 2.grp", "mineral field 3.grp",
         "mineral1.grp", "mineral2.grp", "mineral3.grp", "MinField.grp", "MinField1.grp",
         "bunker.grp", "Bunker.grp", "bunkelT.grp", "turret.grp", "missile turret.grp",
         "vulture.grp", "wraith.grp", "valkyrie.grp", "science vessel.grp",
         "command center.grp", "comsat station.grp", "nuclear silo.grp",
         "hydralisk.grp", "mutalisk.grp", "zerg hatchery.grp", "creep colony.grp",
         "sunken colony.grp", "spore colony.grp", "spawning pool.grp", "hydralisk den.grp",
         "evolution chamber.grp", "ultralisk cavern.grp", "defiler mound.grp", "nydus canal.grp",
         "greater spire.grp", "spire.grp", "queen's nest.grp", "infested command center.grp",
         "cmdicons.grp", "cmdicon.grp", "command icons.grp", "IconSet.grp", "icons.grp"]
for d in dirs:
    for c in cands:
        n = d + "\\" + c
        t = probe(n)
        if t:
            print("FOUND %-4s %s" % (t, n))

# Also: scan the StarDat hash table for all stored complete paths? Instead, probe tileset dirs
for ts in ["badlands", "platform", "installation", "jungle", "desert", "ice", "twilight"]:
    for ext in ["cv5", "vf4", "vx4", "vr4", "wpe", "pal"]:
        n = "tileset\\%s\\%s.%s" % (ts, ts, ext)
        t = probe(n)
        if t:
            print("FOUND %-4s %s" % (t, n))

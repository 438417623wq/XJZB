"""v2.11 batch B: every zerg GRP in the archives that is not yet accounted for.

The dat-chain route is dead (probe_v211ah.py: 2/34 by chance) and the icon route
is dead (4 of 6 known-good pairings lose to RCluster). But images.tbl *is* the
game's own list of every GRP it loads, so anything the zerg still needs must be
one of its entries. This prints the zerg entries that no unit/building key has
claimed yet, and then probes a list of plausible alternative filenames in all
three archives in case the repack dropped a name from the table.

Usage: python probe_v211ai.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
ARCS = [("patch_rt", "patch_rt.mpq"), ("StarDat", "StarDat.mpq"),
        ("BrooDat", "BrooDat.mpq")]
H = [sc_archive.Archive(os.path.join(ROOT, m)) for _, m in ARCS]
PT, SD, BD = H


def tbl(d):
    cnt = d[0] | (d[1] << 8)
    out = []
    for i in range(cnt):
        o = d[2 + i * 2] | (d[3 + i * 2] << 8)
        e = o
        while e < len(d) and d[e] != 0:
            e += 1
        out.append(d[o:e].decode("latin-1"))
    return out


# every zerg .grp name the project already uses
CLAIMED = set("""avenger zavBirth zavDeath zavExplo brood zbrShad zbrDeath bugguy
zbgShad cocoon defiler zdebirth zdeDeath drone zdrbirth zdrDeath egg zegShad
zegspawn zegDeath guardian zguDeath hydra zhyShad zhybirth zhyDeath uikerr
uikShad larva zlaDeath mutalid zmubirth zmuDeath overlord zovBirth zovDeath
queen zquDeath zquBirth ultra zulShad zulbirth zulDeath zergling zzeShad
zzebirth zzeDeath UCereb zucShad chrysal zchShad cerebrat zceShad fcolony
zfcShad hatchery zhaShad Hive zhiShad Lair zlrShad Lurker zluShad MutaCham
zmcShad Mutapit zmhShad nest zneShad NydusPit znyShad Over1 Over2 RCluster
zrcShad Extract zreShad Snakey zsbShad spire zspShad SColony zscShad Infest03
ZBuild zSpawn01 zSpawn02 zSpawn03 zmarker zCirGlow lurkburr lurknorm LurkEgg
devour Zlurker ZluBirth ZluDeath XOvermnd ZovShad Mutate""".split())

print("=========== zerg entries in each images.tbl ===========")
for (an, _), ar in zip(ARCS, H):
    if not ar.has("arr\\images.tbl"):
        print("--- %s: no images.tbl" % an)
        continue
    t = tbl(ar.read_with_gaps("arr\\images.tbl")[0])
    un = []
    for i, v in enumerate(t):
        low = v.lower().replace("/", "\\")
        if not low.startswith("zerg\\") or not low.endswith(".grp"):
            continue
        base = low.split("\\")[-1][:-4]
        if base in {c.lower() for c in CLAIMED}:
            continue
        un.append((i, v))
    print("--- %s  (%d entries, %d unclaimed zerg .grp)" % (an, len(t), len(un)))
    for i, v in un:
        print("      %-5d %s" % (i, v))
print()

print("=========== direct filename probes (all archives) ===========")
CAND = [
    "unit\\zerg\\Den.grp", "unit\\zerg\\HydraDen.grp", "unit\\zerg\\HydDen.grp",
    "unit\\zerg\\hydraden.grp", "unit\\zerg\\Hydralisk.grp",
    "unit\\zerg\\Cavern.grp", "unit\\zerg\\UltCavern.grp",
    "unit\\zerg\\UltraCavern.grp", "unit\\zerg\\ultcav.grp",
    "unit\\zerg\\EvolCham.grp", "unit\\zerg\\EvoCham.grp",
    "unit\\zerg\\Evolution.grp", "unit\\zerg\\evol.grp",
    "unit\\zerg\\Mound.grp", "unit\\zerg\\DefilerMound.grp",
    "unit\\zerg\\GSpire.grp", "unit\\zerg\\Gspire.grp",
    "unit\\zerg\\Spire2.grp", "unit\\zerg\\spireL.grp",
    "unit\\zerg\\Ultralisk.grp", "unit\\zerg\\UltraDen.grp",
    "unit\\zerg\\Mutate.grp", "unit\\zerg\\Mutalid.grp",
    "unit\\zerg\\uikerr.grp", "unit\\zerg\\bugguy.grp",
]
for c in CAND:
    hits = [an for (an, _), ar in zip(ARCS, H) if ar.has(c)]
    print("  %-34s %s" % (c, ",".join(hits) if hits else "---"))

for ar in H:
    ar.close()

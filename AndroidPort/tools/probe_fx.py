"""Probe which muzzle-flash / smoke / spark effect GRPs this repack actually has."""
import os
import sc_archive

ROOT = r"F:\KF\XJZB"
ARCS = [("PT", "patch_rt.mpq"), ("SD", "StarDat.mpq"), ("BD", "BrooDat.mpq")]
arches = [(n, sc_archive.Archive(os.path.join(ROOT, f))) for n, f in ARCS]

CANDS = [
    r"unit\thingy\tmeFlshS.grp", r"unit\thingy\tmeFlshM.grp", r"unit\thingy\tmeFlshL.grp",
    r"unit\thingy\bsmoke.grp", r"unit\thingy\phit.grp", r"unit\bullet\ephFire.grp",
    r"unit\thingy\tfire.grp", r"unit\thingy\zfire.grp", r"unit\thingy\pfire.grp",
    r"unit\thingy\tspark.grp", r"unit\thingy\phitS.grp", r"unit\thingy\phitM.grp",
    r"unit\thingy\phitL.grp", r"unit\thingy\phitX.grp",
]

for c in CANDS:
    hits = [n for n, a in arches if a.has(c)]
    print("%-40s %s" % (c, hits if hits else "MISS"))

# also scan listfile for anything with 'hit' or 'flsh' or 'spark'
lf = os.path.join(ROOT, r"AndroidPort\tools\listfile_BrooDat.txt")
names = [l.strip() for l in open(lf, encoding="utf8", errors="ignore")]
print("\n--- listfile candidates ---")
for kw in ("hit", "flsh", "spark", "smoke", "fire", "shot", "bldg", "bang", "explo", "flame"):
    hits = [n for n in names if kw in n.lower()]
    if hits:
        print("[%s] %s" % (kw, hits[:20]))

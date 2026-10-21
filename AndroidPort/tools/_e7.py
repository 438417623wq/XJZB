"""Batch E probe 7: dump the race score-screen PCX panels (candidate emblems)."""
import os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, ".")
import sc_archive
import pipeline_sounds as ps

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

groups = []
for race in ("ScoreP", "ScoreT", "ScoreZ"):
    for suf in ("d", "v"):
        names = []
        for i in range(5):
            for pat in ("%s%s%%d.pcx" % (race, suf), "%s%s%%d.PCX" % (race, suf),
                        "%s%s_%%d.pcx" % (race, suf)):
                p = "glue\\" + race + suf + "\\" + (pat % i)
                if SD.has(p) or BD.has(p):
                    names.append(p)
        groups.append((race + suf, names))

for g, names in groups:
    print("%-8s %d hits" % (g, len(names)))
    for p in names:
        print("    ", p)

# brute: list what's actually under glue\Score*
print()
print("=== actual glue\\Score* entries in listfile ===")
with open(os.path.join(ROOT, r"AndroidPort\tools\listfile_BrooDat.txt"), "r",
          encoding="latin-1") as f:
    for line in f:
        line = line.strip()
        if line.lower().startswith("glue\\score"):
            print("   ", line)

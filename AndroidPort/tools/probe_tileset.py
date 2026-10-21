"""Probe tileset file locations under StarDat."""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
PT = sc_archive.Archive(r"F:\KF\XJZB\patch_rt.mpq")

tss = ["badlands", "platform", "installation", "jungle", "desert", "ice", "twilight"]
exts = ["cv5", "vc5", "vf4", "vx4", "vr4", "wpe", "pal", "cvP"]

pats = []
for ts in tss:
    for ext in exts:
        pats.append("tileset\\%s\\%s.%s" % (ts, ts, ext))
        pats.append("tileset\\%s\\%s%s" % (ts, ts, ext))
        pats.append("tileset\\%s.%s" % (ts, ext))
# generic names inside each dir
for ts in tss:
    for base in ["tileset", "palstd", "units", "tiles"]:
        for ext in exts:
            pats.append("tileset\\%s\\%s.%s" % (ts, base, ext))
for base in ["palstd", "palette", "units"]:
    for ext in ["pal", "wpe"]:
        pats.append("%s.%s" % (base, ext))
        pats.append("tileset\\%s.%s" % (base, ext))
        pats.append("tileset\\jungle\\%s.%s" % (base, ext))

found = set()
for p in pats:
    for tag, ar in (("SD", SD), ("PT", PT)):
        if ar.has(p):
            found.add((tag, p))
for tag, p in sorted(found):
    print("FOUND %-3s %s" % (tag, p))
print("total probed:", len(pats))

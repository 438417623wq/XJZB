import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive
from gapio import GapReader
sd = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
cv5, gaps = sd.read_with_gaps("tileset\\platform.cv5")
info = sd.info("tileset\\platform.cv5")
print("read_with_gaps: len(data)=", len(cv5), "recorded size=", info["size"], "gaps=", gaps)
g = GapReader(cv5, gaps)
print("GapReader orig_len?", getattr(g, "orig_len", None))
mine = open(r"F:\KF\XJZB\scr_research\tileset\platform.cv5", "rb").read()
print("my file len", len(mine))
same = 0; diff = 0; firstdiff = None
for i in range(min(len(mine), info["size"])):
    a = mine[i]; b = g.byte(i)
    if a == b: same += 1
    else:
        diff += 1
        if firstdiff is None: firstdiff = i
print("bytes equal:", same, "differ:", diff, "first diff at", firstdiff)
if firstdiff is not None:
    print("  mine:", mine[firstdiff:firstdiff+16].hex(" "))
    print("  gapr:", bytes(g.byte(firstdiff+k) for k in range(16)).hex(" "))

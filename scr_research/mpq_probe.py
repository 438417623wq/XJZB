import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
from mpq import MPQ
root = r"F:\KF\XJZB"
ts = ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]
cands = []
for t in ts:
    for f in ["dddata.bin","cv5.bin","vx4.bin","vr4.bin","wpe.bin"]:
        cands.append(f"tileset\\{t}\\{f}")
    cands.append(f"tileset\\{t}.cv5")
for arc in ["StarDat.mpq","BrooDat.mpq","BroodWar.mpq","patch_rt.mpq"]:
    m = MPQ(os.path.join(root,arc))
    print("=== "+arc)
    for c in cands:
        if m.has(c):
            inf = m.info(c)
            print(f"   FOUND {c}  size={inf['size']} csize={inf['csize']} flags={inf['flags']:#x}")
    m.close()

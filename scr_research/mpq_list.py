import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
from mpq import MPQ
root = r"F:\KF\XJZB"
for arc in ["StarDat.mpq", "BrooDat.mpq", "BroodWar.mpq", "patch_rt.mpq"]:
    p = os.path.join(root, arc)
    try:
        m = MPQ(p)
    except Exception as e:
        print(f"{arc}: OPEN FAIL {e}"); continue
    lf = m.listfile()
    print(f"{arc}: fmt={m.format_version} files_in_listfile={len(lf)}")
    hits = [n for n in lf if any(k in n.lower() for k in ("dddata", "cv5", "tileset", "vx4", "vr4", "wpe"))]
    for n in hits[:80]:
        print("   ", n)
    m.close()

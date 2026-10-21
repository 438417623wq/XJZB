import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive
TS = ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]
for mpq in [r"F:\KF\XJZB\StarDat.mpq", r"F:\KF\XJZB\BrooDat.mpq"]:
    ar = sc_archive.Archive(mpq)
    print("===", os.path.basename(mpq))
    for ts in TS:
        found = []
        for cand in [f"tileset\\{ts}\\dddata.bin", f"tileset\\{ts.capitalize()}\\dddata.bin",
                     f"tileset\\{ts}.dddata.bin"]:
            try:
                d,g = ar.read_with_gaps(cand)
                found.append(f"{cand}({len(d)}B)")
            except Exception: pass
        print(f"   {ts:9s} dddata: {found if found else 'NOT FOUND'}")

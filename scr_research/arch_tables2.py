import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive
print([m for m in dir(sc_archive.Archive) if not m.startswith("_")])
for mpq in [r"F:\KF\XJZB\StarDat.mpq", r"F:\KF\XJZB\BrooDat.mpq"]:
    print("===", os.path.basename(mpq))
    ar = sc_archive.Archive(mpq)
    for ts in ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]:
        row = []
        for ext in ("dddata.bin", "cv5"):
            try:
                d, g = ar.read_with_gaps(f"tileset\\{ts}.{ext}")
                row.append(f"{ext}:OK({len(d)}B,gaps={len(g)})")
            except Exception as e:
                row.append(f"{ext}:NO")
        print(f"   {ts:9s} " + "  ".join(row))

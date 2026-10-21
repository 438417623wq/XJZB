import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive
for mpq in [r"F:\KF\XJZB\StarDat.mpq", r"F:\KF\XJZB\BrooDat.mpq"]:
    print("===", os.path.basename(mpq))
    try:
        ar = sc_archive.Archive(mpq)
        names = ar.list_files() if hasattr(ar, "list_files") else None
        if names is None:
            names = getattr(ar, "files", None) or []
        print("   total entries:", len(names))
        dd = [n for n in names if "dddata" in n.lower()]
        cv = [n for n in names if n.lower().endswith(".cv5")]
        sp = [n for n in names if "sprites.dat" in n.lower()]
        print("   dddata.bin:", dd)
        print("   cv5 count:", len(cv), sorted(cv)[:10])
        print("   sprites.dat:", sp)
    except Exception as e:
        print("   ERROR", type(e).__name__, e)

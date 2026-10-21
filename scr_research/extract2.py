import sys, os, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
from sc_archive import Archive
root = r"F:\KF\XJZB"
out = r"F:\KF\XJZB\scr_research\tileset"
os.makedirs(out, exist_ok=True)
plan = {"StarDat.mpq": ["badlands","platform","install","ashworld","jungle"],
        "BrooDat.mpq": ["desert","ice","twilight"]}
for arc, tss in plan.items():
    a = Archive(os.path.join(root, arc))
    for t in tss:
        for name, fn in ((f"tileset\\{t}.cv5", f"{t}.cv5"), (f"tileset\\{t}\\dddata.bin", f"{t}.dddata.bin")):
            if not a.has(name):
                print("MISS", name); continue
            try:
                data = a.read(name)
            except Exception as e:
                print("FAIL", name, e); continue
            open(os.path.join(out, fn), "wb").write(data)
            print(f"{fn:22s} {len(data):8d} bytes")
    a.close()

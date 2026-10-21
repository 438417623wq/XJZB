import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
from mpq import MPQ
root = r"F:\KF\XJZB"
out = r"F:\KF\XJZB\scr_research\tileset"
os.makedirs(out, exist_ok=True)
plan = {"StarDat.mpq": ["badlands","platform","install","ashworld","jungle"],
        "BrooDat.mpq": ["desert","ice","twilight"]}
for arc, tss in plan.items():
    m = MPQ(os.path.join(root, arc))
    for t in tss:
        for ext in ("cv5","dddata.bin"):
            name = f"tileset\\{t}.{ext}" if ext=="cv5" else f"tileset\\{t}\\{ext}"
            data = m.read(name)
            fn = os.path.join(out, f"{t}." + ("cv5" if ext=="cv5" else "dddata.bin"))
            open(fn,"wb").write(data)
            print(f"{t:10s} {ext:12s} {len(data):8d} bytes  -> {os.path.basename(fn)}")
    m.close()

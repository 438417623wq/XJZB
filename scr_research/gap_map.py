import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
from sc_archive import Archive
root = r"F:\KF\XJZB"
plan = {"StarDat.mpq": ["badlands","platform","install","ashworld","jungle"],
        "BrooDat.mpq": ["desert","ice","twilight"]}
for arc, tss in plan.items():
    a = Archive(os.path.join(root, arc))
    for t in tss:
        name = f"tileset\\{t}\\dddata.bin"
        data, gaps = a.read_with_gaps(name)
        inf = a.info(name)
        print(f"--- {t} recorded={inf['size']} got={len(data)} gaps={len(gaps)}")
        for pos, size in sorted(gaps):
            e0, e1 = pos//512, (pos+size-1)//512
            print(f"    gap at byte {pos}..{pos+size-1} (size {size}) -> entries {e0}..{e1}")
    a.close()

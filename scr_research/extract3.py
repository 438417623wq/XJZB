import sys, os, struct, json
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
            if not a.has(name): print("MISS", name); continue
            data, gaps = a.read_with_gaps(name)
            inf = a.info(name)
            # pad gaps with zeros to restore the recorded size
            buf = bytearray(data)
            for pos, size in gaps:
                if pos > len(buf): buf += bytes(pos-len(buf))
                buf[pos:pos+size] = bytes(size)
            if len(buf) < inf["size"]: buf += bytes(inf["size"]-len(buf))
            open(os.path.join(out, fn), "wb").write(bytes(buf))
            print(f"{fn:22s} got={len(data):8d} padded={len(buf):8d} recorded={inf['size']:8d} gaps={len(gaps)}")
    a.close()

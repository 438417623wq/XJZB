import sys, os, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
root = r"F:\KF\XJZB"
targets = ["StarEdit.exe", "StarCraft.exe", "Brood.exe", "patch_rt.mpq", "storm.dll"]
for t in targets:
    p = os.path.join(root, t)
    if not os.path.exists(p): print(t, "MISSING"); continue
    d = open(p, "rb").read()
    res = {}
    for tag in (b"DD2 ", b"DDATA", b"dddata.bin", b"tileset\\", b"IVE2", b"SWNM", b"MBRF", b"CV5"):
        c = d.count(tag)
        if c: res[tag.decode("latin1")] = c
    print(f"{t}: {res}")

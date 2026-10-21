import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive
from gapio import GapReader
ar = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
data, gaps = ar.read_with_gaps("tileset\\platform.cv5")
g = GapReader(data, gaps)
for k in (1024, 1025, 1030, 1254, 1441, 1450):
    rec = bytes(g.byte(k*52+i) for i in range(52))
    u = struct.unpack_from("<26H", rec)
    print(f"group {k}:")
    print("   u16:", u)
    print("   hex:", rec.hex(" "))

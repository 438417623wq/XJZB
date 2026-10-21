import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive
from gapio import GapReader
for arch, names in ((r"F:\KF\XJZB\StarDat.mpq", ["badlands","platform","install","ashworld","jungle"]),
                    (r"F:\KF\XJZB\BrooDat.mpq", ["desert","ice","twilight"])):
    ar = sc_archive.Archive(arch)
    for ts in names:
        data, gaps = ar.read_with_gaps("tileset\\%s.cv5" % ts)
        size = ar.info("tileset\\%s.cv5" % ts)["size"]
        g = GapReader(data, gaps)
        n = size // 52
        ones = [k for k in range(n) if g.u16(k*52) == 1]
        dd = [k for k in ones if g.u16(k*52+2) & 0x3000]
        print(f"{ts:9s} size={size:6d} groups={n:5d} offset0==1: {len(ones):4d} first={ones[:12]}  with_overlayflag={len(dd)}")

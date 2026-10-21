"""Try to parse dddata.bin as a self-describing stream of vector sets:
{u16 n, n * (u16, u16) pairs} with various zero-handling rules; success =
the parse consumes the file exactly (to EOF) with plausible n values.
"""
import struct

import sc_archive
from gapio import GapReader

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")


def read(name):
    d, gaps = SD.read_with_gaps(name)
    return GapReader(d, gaps)


for ts in ("badlands", "jungle", "platform", "ashworld", "install"):
    d, gaps = SD.read_with_gaps("tileset\\%s\\dddata.bin" % ts)
    g = GapReader(d, gaps)
    print("--- %s size=%d ---" % (ts, len(d)))
    # rule A: n=0 -> skip 2 bytes and continue
    for rule in ("skip2", "skip64", "stop"):
        p = 0
        sets = 0
        maxn = 0
        ok = True
        while p < len(d) - 1:
            n = g.u16(p)
            if n > 512:
                ok = False
                break
            if n == 0:
                if rule == "stop":
                    break
                p += 2 if rule == "skip2" else 64
                sets += 1
                continue
            maxn = max(maxn, n)
            p += 2 + n * 4
            sets += 1
        print("  rule=%-6s consumed=%d/%d sets=%d maxn=%d exact=%s"
              % (rule, p, len(d), sets, maxn, p == len(d) or (rule != "stop" and p >= len(d) - 1)))

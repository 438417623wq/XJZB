"""Dump arr/portdata.tbl from StarDat + BrooDat: the authoritative list of
portrait SMK paths. portdata.dat maps portrait id -> file/dir, but for
extraction the tbl's path strings are what we need."""
import sc_archive
from gapio import GapReader

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
BD = sc_archive.Archive(r"F:\KF\XJZB\BrooDat.mpq")


def parse_tbl(data, gaps):
    g = GapReader(data, gaps)
    n = g.u16(0)
    offs = [g.u16(2 + i * 2) for i in range(n)]
    out = []
    for o in offs:
        chars = bytearray()
        p = o
        for _ in range(300):
            c = g.byte(p)
            if c == 0:
                break
            chars.append(c)
            p += 1
        out.append(chars.decode("cp1252", "replace"))
    return out


names = []
for tag, ar in (("SD", SD), ("BD", BD)):
    d, gaps = ar.read_with_gaps(r"arr\portdata.tbl")
    for s in parse_tbl(d, gaps):
        if s.lower() not in {x.lower() for x in names}:
            names.append(s)
    print(tag, "portdata.tbl entries:", len(names), "cumulative")

import io
with io.open("portdata_tbl.txt", "w", encoding="utf8") as fp:
    for i, s in enumerate(names):
        fp.write("%d\t%s\n" % (i, s))
print("written portdata_tbl.txt")
for s in names:
    if "fid" in s.lower() or "smk" in s.lower():
        print("  ", s)

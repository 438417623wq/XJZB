"""v2.11 batch B: read the real unit names out of rez\\stat_txt.tbl.

Every building identity question in batch B is a naming question, and the names
live in one file: stat_txt.tbl is a TBL string table whose entry order matches
units.dat, so entry N is the name of units.dat id N. cmdicons.grp uses the same
index, which is what makes `icon id == units.dat id` true.

Reads the table straight out of the archives (patch -> StarDat -> BrooDat) and
prints ids 105..175, i.e. the terran buildings through the zerg ones.

Usage: python probe_v211s.py [firstId] [lastId]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

CANDIDATES = ["rez\\stat_txt.tbl", "rez\\stat_txt.TBL", "arr\\stat_txt.tbl"]


def find():
    for path in CANDIDATES:
        for ar in (PT, SD, BD):
            if ar.has(path):
                data, _ = ar.read_with_gaps(path)
                print("found %s in %s (%d bytes)" % (path, ar.path, len(data)))
                return data
    return None


def read_tbl(data):
    """StarCraft TBL: u16 count, u16 offset[count], then NUL-terminated strings."""
    if len(data) < 4:
        return []
    count = data[0] | (data[1] << 8)
    if count == 0 or 4 + count * 2 > len(data):
        return []
    offs = [(data[2 + i * 2] | (data[3 + i * 2] << 8)) for i in range(count)]
    out = []
    for off in offs:
        if off >= len(data):
            out.append("")
            continue
        end = data.find(b"\x00", off)
        if end < 0:
            end = len(data)
        out.append(data[off:end].decode("cp1252", "replace"))
    return out


data = find()
if data is None:
    print("stat_txt.tbl not found in any archive")
    sys.exit(1)

names = read_tbl(data)
print("entries: %d" % len(names))

lo = int(sys.argv[1]) if len(sys.argv) > 1 else 105
hi = int(sys.argv[2]) if len(sys.argv) > 2 else 175
for i in range(lo, min(hi + 1, len(names))):
    if names[i].strip():
        print("%4d  %s" % (i, names[i]))

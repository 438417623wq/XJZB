"""v2.11 batch B: dump arr\\images.tbl, the image-id -> GRP path table.

probe_v211s.py proved the TBL reader works (rez\\stat_txt.tbl decoded to exactly
the real unit names, indexed by units.dat id). images.tbl is the same format but
holds GRP paths indexed by image id, which is the missing link between a GRP
file name and a units.dat building id.

Usage: python probe_v211v.py [firstId] [lastId]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))


def read_tbl(data):
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


path = "arr\\images.tbl"
data = None
src = None
for ar in (PT, SD, BD):
    if ar.has(path):
        data, _ = ar.read_with_gaps(path)
        src = ar.path
        break
if data is None:
    print("images.tbl not found")
    sys.exit(1)

names = read_tbl(data)
print("images.tbl from %s: %d bytes, %d entries" % (src, len(data), len(names)))

lo = int(sys.argv[1]) if len(sys.argv) > 1 else 0
hi = int(sys.argv[2]) if len(sys.argv) > 2 else len(names) - 1
for i in range(lo, min(hi + 1, len(names))):
    n = names[i]
    if n.strip() and "zerg" in n.lower():
        print("%4d  %s" % (i, n))

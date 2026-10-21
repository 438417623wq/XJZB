"""v2.11: dump arr\\images.tbl raw rows for a range, both archives."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
lo = int(sys.argv[1]) if len(sys.argv) > 1 else 55
hi = int(sys.argv[2]) if len(sys.argv) > 2 else 135

for tag, fn in (("SD", "StarDat.mpq"), ("BD", "BrooDat.mpq")):
    ar = sc_archive.Archive(os.path.join(ROOT, fn))
    data, _ = ar.read_with_gaps("arr\\images.tbl")
    cnt = data[0] | (data[1] << 8)
    offs = [data[2 + 2 * k] | (data[3 + 2 * k] << 8) for k in range(cnt)]
    print("== %s cnt=%d bytes=%d" % (tag, cnt, len(data)))
    for i in range(lo, min(hi, cnt)):
        o = offs[i]
        e = data[o:data.index(b"\x00", o)].decode("cp1252", "replace")
        print("  %3d %s" % (i, e))
    ar.close()

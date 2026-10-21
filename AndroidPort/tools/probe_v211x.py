"""v2.11 batch B: resolve building GRPs through sprites.dat -> images.tbl.

units.dat is not readable here (probe_v211w.py found no self-consistent record
stride, and the decoded head is letter soup), but the chain has a shortcut:
StarCraft keeps sprites.dat in units.dat order, so sprite index == units.dat id.
sprites.dat's first field is an image id, and images.tbl maps image id -> GRP
path (probe_v211v.py proved that table decodes to real paths, e.g. entry 61
zerg\\UCereb.grp).

So: read sprites.dat[135], look up images.tbl of that value, and the GRP for
units.dat id 135 (Zerg Hydralisk Den) falls out. The already-known rows are the
control -- 131 must come back hatchery.grp, 141 spire.grp, 149 Extract.grp.

Usage: python probe_v211x.py [lo] [hi]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))


def read(path, order=(BD, PT, SD)):
    for ar in order:
        if ar.has(path):
            data, _ = ar.read_with_gaps(path)
            return data
    return None


def read_tbl(data):
    count = data[0] | (data[1] << 8)
    offs = [(data[2 + i * 2] | (data[3 + i * 2] << 8)) for i in range(count)]
    out = []
    for off in offs:
        if off >= len(data):
            out.append("")
            continue
        end = data.find(b"\x00", off)
        out.append(data[off:end].decode("cp1252", "replace") if end > 0 else "")
    return out


def u16(d, o):
    return d[o] | (d[o + 1] << 8)


img = read("arr\\images.tbl")
if img is None:
    print("images.tbl missing")
    sys.exit(1)
images = read_tbl(img)
print("images.tbl: %d entries" % len(images))

for tag, ar in (("StarDat", SD), ("BrooDat", BD)):
    dat = read("arr\\sprites.dat", order=(ar,))
    if dat is None:
        print("%s: no sprites.dat" % tag)
        continue
    print()
    print("=== %s sprites.dat %d bytes ===" % (tag, len(dat)))
    # pick the stride whose image ids are all inside images.tbl
    best = None
    for R in range(4, 33):
        n = len(dat) // R
        if n < 160:
            continue
        vals = [u16(dat, i * R) for i in range(n)]
        bad = sum(1 for v in vals if v >= len(images))
        if best is None or bad < best[0]:
            best = (bad, R, n, vals)
    if best is None:
        print("  no stride candidate")
        continue
    bad, R, n, vals = best
    print("  stride=%d records=%d out-of-range=%d" % (R, n, bad))
    if bad:
        print("  (out-of-range means the stride is wrong -- treat the rest as noise)")
    for i in range(int(sys.argv[1]) if len(sys.argv) > 1 else 128,
                   int(sys.argv[2]) if len(sys.argv) > 2 else 152):
        if i < n:
            print("  sprite %3d -> image %4d  %s" % (i, vals[i], images[vals[i]]))

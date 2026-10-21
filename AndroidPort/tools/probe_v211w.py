"""v2.11 batch B: parse arr\\units.dat, the authoritative unit/building table.

Visual identity matching is exhausted: shape IoU against the command-card
wireframe recovered only 2 of the 6 already-shipping pairs, and the four zerg
buildings batch B needs (Hydralisk Den 135, Defiler Mound 136, Evolution Chamber
139, Ultralisk Cavern 140) still have no GRP.

units.dat is the authority. Its records start with the unit's own id as a u16, so
the record size falls out of the file without any documentation: find R such that
u16 at i*R == i for i = 0..n. Then read the name string id and the flingy id out
of each record, follow flingy -> sprite -> image, and read the GRP path from
images.tbl (probe_v211v.py proved that table decodes to real GRP paths).

Usage: python probe_v211w.py [datPath] [ids...]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))


def read(path, prefer=BD):
    for ar in (prefer, PT, SD, BD):
        if ar.has(path):
            data, _ = ar.read_with_gaps(path)
            return data
    return None


def read_tbl(data):
    count = data[0] | (data[1] << 8)
    offs = [(data[2 + i * 2] | (data[3 + i * 2] << 8)) for i in range(count)]
    out = []
    for off in offs:
        end = data.find(b"\x00", off) if off < len(data) else -1
        out.append(data[off:end].decode("cp1252", "replace") if end > 0 else "")
    return out


def find_record_size(data, maxr=256):
    """units.dat records begin with their own u16 id -- that pins the stride."""
    best = []
    for r in range(8, maxr):
        ok = 0
        for i in range(1, 40):
            off = i * r
            if off + 2 > len(data):
                break
            v = data[off] | (data[off + 1] << 8)
            if v == i:
                ok += 1
        if ok >= 30:
            best.append((ok, r))
    return sorted(best, reverse=True)


dat = read("arr\\units.dat")
if dat is None:
    print("units.dat not found")
    sys.exit(1)
print("units.dat %d bytes" % len(dat))

cands = find_record_size(dat)
print("record-size candidates (matched, stride): %s" % cands[:5])
if not cands:
    sys.exit(1)
R = cands[0][1]
n = len(dat) // R
print("stride R=%d -> %d records (remainder %d)" % (R, n, len(dat) % R))

# the label string id sits somewhere in the record; find the offset whose value
# equals a known id: 106 Command Center, 131 Hatchery, 141 Spire.
def u16(rec, off):
    return rec[off] | (rec[off + 1] << 8)


KNOWN = {106: "Terran Command Center", 131: "Zerg Hatchery", 141: "Zerg Spire",
         7: "Terran SCV", 37: "Zerg Zergling", 65: "Protoss Zealot"}
name_off = None
for off in range(0, R - 1, 2):
    if all(u16(dat[i * R:(i + 1) * R], off) == i for i in KNOWN):
        name_off = off
        break
print("label-string-id offset = %s" % name_off)

stat = read("rez\\stat_txt.tbl", PT)
names = read_tbl(stat)

ids = [int(x) for x in sys.argv[2:]] or [135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 146, 149, 151, 152]
print()
print("units.dat id  flingy  name")
for i in ids:
    if i >= n:
        continue
    rec = dat[i * R:(i + 1) * R]
    fl = u16(rec, 0x10)
    nm = ""
    if name_off is not None:
        s = u16(rec, name_off)
        nm = names[s] if s < len(names) else "?"
    print("%11d  %6d  %s" % (i, fl, nm))

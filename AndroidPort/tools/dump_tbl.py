"""Dump the whole images.tbl with archive availability, and fix images.dat size."""
import struct
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
BD = sc_archive.Archive(r"F:\KF\XJZB\BrooDat.mpq")
PT = sc_archive.Archive(r"F:\KF\XJZB\patch_rt.mpq")


def parse_tbl(data):
    n, = struct.unpack_from("<H", data, 0)
    offs = struct.unpack_from("<%dH" % n, data, 2)
    out = []
    for i in range(n):
        s = data[offs[i]:data.find(b"\0", offs[i])]
        out.append(s.decode("latin1"))
    return out


names = parse_tbl(SD.read("arr\\images.tbl"))

for i, s in enumerate(names):
    if not s.endswith(".grp"):
        continue
    full = "unit\\" + s
    where = []
    for tag, ar in (("SD", SD), ("BD", BD), ("PT", PT)):
        if ar.has(full):
            where.append(tag)
    print("%4d %-40s %s" % (i, s, ",".join(where) if where else "-"))

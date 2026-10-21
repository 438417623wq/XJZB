"""Parse images.tbl (string table) and dump the GRP names the game itself uses.

Also probes which archive carries each file and inspects images.dat layout.
"""
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
print("images.tbl entries:", len(names))
for i in range(0, 40):
    print("  %4d %s" % (i, names[i]))
print("  ...")
# show some known-interesting ones
for pat in ("marine", "zergling", "command", "mineral", "cmdicons", "depot", "hydral"):
    hits = [(i, s) for i, s in enumerate(names) if pat in s.lower()]
    print("PATTERN %s: %s" % (pat, hits[:12]))

dat = SD.read("arr\\images.dat")
print("images.dat size:", len(dat))
# find record size: assume first u32 of each record is a valid tbl index
for rec in range(8, 64):
    if (len(dat) - 2) % rec == 0:
        cnt = (len(dat) - 2) // rec
        ok = 0
        for e in range(min(cnt, 40)):
            fid, = struct.unpack_from("<I", dat, 2 + e * rec)
            if fid < len(names):
                ok += 1
        if ok == min(cnt, 40):
            print("candidate record size", rec, "count", cnt)

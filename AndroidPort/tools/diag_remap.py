"""Settle the effect-palette question from the game's own data.

(a) hexdump the ofire.pcx header to learn its true shape,
(b) find the images.dat record for tmeFlshS and read its remap byte.
"""
import os
import struct
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))


def parse_tbl(data):
    n, = struct.unpack_from("<H", data, 0)
    offs = struct.unpack_from("<%dH" % n, data, 2)
    return [data[offs[i]:data.find(b"\0", offs[i])].decode("latin1") for i in range(n)]


print("=== ofire.pcx header (platform) ===")
for ar, nm in ((SD, "StarDat"), (BD, "BrooDat")):
    p = r"tileset\platform\ofire.pcx"
    if ar.has(p):
        d, _ = ar.read_with_gaps(p)
        print(nm, "len", len(d), "magic", d[:4].hex())
        xmin, ymin, xmax, ymax = struct.unpack_from("<HHHH", d, 4)
        print("  xmin=%d ymin=%d xmax=%d ymax=%d -> %dx%d" %
              (xmin, ymin, xmax, ymax, xmax - xmin + 1, ymax - ymin + 1))
        print("  bytes/pixel=%d nplanes=%d" % (d[3], d[65]))
        print("  first 32 payload bytes:", d[128:160].hex())
        print("  palette tail first 12 entries:",
              [tuple(d[-768 + i * 3: -768 + i * 3 + 3]) for i in range(4)])
        break

print("\n=== images.dat: locate tmeFlshS / BangS records ===")
for ar, nm in ((SD, "StarDat"), (BD, "BrooDat")):
    try:
        names = parse_tbl(ar.read("arr\\images.tbl"))
        dat = ar.read("arr\\images.dat")
    except Exception as e:
        print(nm, "fail", e)
        continue
    print("%s images.tbl=%d images.dat=%d" % (nm, len(names), len(dat)))
    targets = [i for i, s in enumerate(names)
               if "flsh" in s.lower() or "bang" in s.lower() or "bsmoke" in s.lower()]
    for t in targets:
        print("   tbl[%d] = %s" % (t, names[t]))
    # find u32 occurrences of each target index in images.dat
    for t in targets:
        pat = struct.pack("<I", t)
        pos = []
        start = 0
        while True:
            i = dat.find(pat, start)
            if i < 0 or len(pos) > 4:
                break
            pos.append(i)
            start = i + 1
        for p in pos:
            lo = max(0, p - 8)
            ctx = dat[lo:p + 24]
            print("     idx %-4d at %-6d ctx=%s" % (t, p, ctx.hex()))

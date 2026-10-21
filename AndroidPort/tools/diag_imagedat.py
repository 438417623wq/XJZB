"""Resolve the effect palette question from the game's own data.

images.tbl lists GRP names; images.dat has one record per image with a `remap`
field that selects a special palette (ofire/gfire/bfire/...). If the flash and
bang records carry a remap, effects must be recoloured through that ramp rather
than drawn with the terrain palette.
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
    out = []
    for i in range(n):
        end = data.find(b"\0", offs[i])
        out.append(data[offs[i]:end].decode("latin1"))
    return out


for label, ar in (("StarDat", SD), ("BrooDat", BD)):
    try:
        names = parse_tbl(ar.read("arr\\images.tbl"))
    except Exception as e:
        print(label, "images.tbl fail", e)
        continue
    print("=== %s images.tbl: %d entries ===" % (label, len(names)))
    hits = [(i, s) for i, s in enumerate(names) if "flsh" in s.lower()
            or "bang" in s.lower() or "smoke" in s.lower() or "ephfire" in s.lower()]
    for i, s in hits:
        print("   %4d %s" % (i, s))
    if not hits:
        print("   (no flsh/bang/smoke entries)")

# images.dat record layout probe on StarDat
try:
    dat = SD.read("arr\\images.dat")
    names = parse_tbl(SD.read("arr\\images.tbl"))
    print("\nimages.dat size", len(dat), "names", len(names))
    for rec in range(8, 64):
        if (len(dat) - 2) % rec:
            continue
        cnt = (len(dat) - 2) // rec
        ok = all(struct.unpack_from("<I", dat, 2 + e * rec)[0] < len(names)
                 for e in range(min(cnt, 60)))
        if ok:
            print("record size %d, count %d" % (rec, cnt))
            for e in range(0, 12):
                base = 2 + e * rec
                vals = struct.unpack_from("<%dB" % rec, dat, base)
                gidx, = struct.unpack_from("<I", dat, base)
                print("  e=%-4d grp=%-4d %s  <- %s" % (e, gidx, vals[4:12], names[gidx]))
            break
except Exception as ex:
    print("images.dat fail", ex)

import struct
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")
print(d[:48].hex())
fc, mw, mh = struct.unpack_from("<HHH", d, 0)
print("fc=%d w=%d h=%d" % (fc, mw, mh))
print("offs@8:", struct.unpack_from("<3I", d, 8))
print("offs@6:", struct.unpack_from("<2I", d, 6))
# maybe table is u32 relative to file start with 2-byte shift: try every offset base 0..8
for base in range(0, 10, 2):
    vals = struct.unpack_from("<4I", d, base + 6) if base + 22 <= len(d) else ()
    print("base", base, vals)

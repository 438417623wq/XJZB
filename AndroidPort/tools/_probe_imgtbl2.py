import struct, sc_archive
ROOT = r"F:\KF\XJZB"
A = sc_archive.Archive(ROOT + r"\BrooDat.mpq")
d = A.read(r"arr\images.tbl")
n = struct.unpack_from("<H", d, 0)[0]
offs = struct.unpack_from("<%dH" % n, d, 2)
strs = []
for o in offs:
    end = d.index(b"\x00", o)
    strs.append(d[o:end].decode("latin-1"))
for i in list(range(230, 250)) + list(range(280, 360)):
    print(i, strs[i])
A.close()

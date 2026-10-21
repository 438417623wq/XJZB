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
print("count", n)
pats = ("covert", "control", "machine", "physics", "silo", "comsat", "nuke", "addon")
for i, s in enumerate(strs):
    low = s.lower()
    if any(p in low for p in pats):
        print(i, repr(s))
A.close()

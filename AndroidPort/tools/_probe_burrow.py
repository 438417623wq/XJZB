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
A.close()
for i, s in enumerate(strs):
    low = s.lower()
    if "zerg" in low and ("bur" in low or "hide" in low or "sub" in low):
        print(i, s)
print("--- zerg grps ---")
for i, s in enumerate(strs):
    low = s.lower()
    if low.startswith("zerg\\") and low.endswith(".grp"):
        print(i, s)

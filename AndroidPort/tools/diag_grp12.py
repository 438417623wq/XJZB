import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")

fc = int.from_bytes(d[0:2], "little")
print("total frames:", fc, "size:", len(d))
# print all frame headers compactly
for fi in range(0, 24):
    base = 6 + fi * 8
    x, y, w, h = d[base], d[base + 1], d[base + 2], d[base + 3]
    off = int.from_bytes(d[base + 4:base + 8], "little")
    print("f%03d box=(%2d,%2d) %2dx%-2d off=%5d" % (fi, x, y, w, h, off))

fi = 10
base = 6 + fi * 8
off = int.from_bytes(d[base + 4:base + 8], "little")
h = d[base + 3]
w = d[base + 2]
lo = [int.from_bytes(d[off + i * 2:off + i * 2 + 2], "little") for i in range(h)]
print("frame10 w=%d h=%d off=%d" % (w, h, off))
print("line_offs:", lo)
print("last+data extends to:", off + lo[-1] + 20, "vs next frame off 4500")

# hex dump of the first 3 rows region
p0 = off + lo[0]
print("rows region hex:")
print(d[p0:p0 + 40].hex())

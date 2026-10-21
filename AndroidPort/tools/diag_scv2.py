"""Dump SCV frame headers and f12 table raw bytes."""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\SCV.grp")
fc = int.from_bytes(d[0:2], "little")
mw = int.from_bytes(d[2:4], "little")
mh = int.from_bytes(d[4:6], "little")
print("SCV frames=%d canvas=%dx%d size=%d" % (fc, mw, mh, len(d)))

for fi in range(min(fc, 20)):
    base = 6 + fi * 8
    x, y, w, h = d[base], d[base + 1], d[base + 2], d[base + 3]
    off = int.from_bytes(d[base + 4:base + 8], "little")
    print("f%02d box=(%2d,%2d) %2dx%-2d off=%5d  hdr=%s" % (fi, x, y, w, h, off, d[base:base + 8].hex()))

fi = 12
base = 6 + fi * 8
off = int.from_bytes(d[base + 4:base + 8], "little")
print("f12 table raw [off..off+40]:", d[off:off + 40].hex())
print("f12 bytes before table [off-8..off]:", d[off - 8:off].hex())

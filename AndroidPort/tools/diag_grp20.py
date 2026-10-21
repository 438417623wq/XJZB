"""Examine the boundary between consecutive frame data blocks."""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")

frames = []
for fi in range(12):
    base = 6 + fi * 8
    x, y, w, h = d[base], d[base + 1], d[base + 2], d[base + 3]
    off = int.from_bytes(d[base + 4:base + 8], "little")
    frames.append((fi, x, y, w, h, off))

for i in range(len(frames)):
    fi, x, y, w, h, off = frames[i]
    lo = [int.from_bytes(d[off + j * 2:off + j * 2 + 2], "little") for j in range(h)]
    print("f%02d off=%5d h=%2d lo[0]=%3d lo[-1]=%3d  data_end_if_rows_at_lo=%5d" % (
        fi, off, h, lo[0], lo[-1], off + lo[-1] + 40))

# hex around 4038..4050 (f9 tail -> f10 table)
print("bytes 4030..4050:", d[4030:4050].hex())
print("bytes 2270..2290:", d[2270:2290].hex())
print("bytes 1834..1846:", d[1834:1846].hex())

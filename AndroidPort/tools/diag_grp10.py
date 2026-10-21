import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")

for fi in (0, 9, 10, 12, 19):
    base = 6 + fi * 8
    xoff, yoff, w, h = d[base], d[base + 1], d[base + 2], d[base + 3]
    off = int.from_bytes(d[base + 4:base + 8], "little")
    line_offs = [int.from_bytes(d[off + i * 2:off + i * 2 + 2], "little") for i in range(h)]
    print("frame %d: box=(%d,%d) %dx%d off=%d deltas=%s" % (
        fi, xoff, yoff, w, h, off,
        [line_offs[i + 1] - line_offs[i] for i in range(min(5, h - 1))]))
    print("   raw row0 (%d B): %s" % (line_offs[1] - line_offs[0],
                                      d[off + line_offs[0]:off + line_offs[1]].hex()))
    if h > 2:
        print("   raw row1 (%d B): %s" % (line_offs[2] - line_offs[1],
                                          d[off + line_offs[1]:off + line_offs[2]].hex()))

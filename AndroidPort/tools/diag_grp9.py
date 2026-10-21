import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")

for fi in (0, 10, 12, 14, 16, 19):
    base = 6 + fi * 8
    xoff, yoff, w, h = d[base], d[base + 1], d[base + 2], d[base + 3]
    off = int.from_bytes(d[base + 4:base + 8], "little")
    line_offs = [int.from_bytes(d[off + i * 2:off + i * 2 + 2], "little") for i in range(h)]
    print("frame %d: box=(%d,%d) %dx%d off=%d lines[0:6]=%s" % (fi, xoff, yoff, w, h, off, line_offs[:6]))
    # dump row 0 ops
    p = off + line_offs[0]
    row_end = off + line_offs[1]
    ops = []
    x = 0
    while p < row_end and len(ops) < 20:
        b = d[p]
        p += 1
        if b & 0x80:
            ops.append("skip%d" % (b & 0x7F))
            x += b & 0x7F
        elif b & 0x40:
            c = d[p]
            p += 1
            ops.append("run%d:%d" % (b & 0x3F, c))
            x += b & 0x3F
        else:
            ops.append("copy%d" % b)
            p += b
            x += b
    print("   ops:", ops, "final x=%d (w=%d)" % (x, w))

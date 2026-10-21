import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")
fc = int.from_bytes(d[0:2], "little")


def frame_info(fi):
    base = 6 + fi * 8
    return (d[base], d[base + 1], d[base + 2], d[base + 3],
            int.from_bytes(d[base + 4:base + 8], "little"))


bad = []
for fi in range(fc):
    try:
        xoff, yoff, w, h, off = frame_info(fi)
        line_offs = [int.from_bytes(d[off + i * 2:off + i * 2 + 2], "little") for i in range(h)]
        for row in range(h):
            p = off + line_offs[row]
            row_end = (off + line_offs[row + 1]) if row + 1 < h else len(d)
            x = 0
            while x < w and p < row_end:
                b = d[p]
                p += 1
                if b & 0x80:
                    x += b & 0x7F
                elif b & 0x40:
                    p += 1
                    x += b & 0x3F
                else:
                    p += b
                    x += b
            if x > w:
                raise ValueError("overshoot row %d x=%d" % (row, x))
    except Exception as e:
        bad.append((fi, str(e)))
print("bad frames: %d / %d" % (len(bad), fc))
for fi, e in bad[:12]:
    xoff, yoff, w, h, off = frame_info(fi)
    print("  frame %d (%dx%d off=%d): %s" % (fi, w, h, off, e))

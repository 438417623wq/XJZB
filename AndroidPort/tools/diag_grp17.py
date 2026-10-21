"""Test the '-2' row-offset rule across several marine frames."""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")


def decode_px(p, w):
    px = 0
    start = p
    while px < w:
        if p >= len(d):
            return None
        b = d[p]
        p += 1
        if b & 0x80:
            px += b & 0x7F
        elif b & 0x40:
            px += (b & 0x3F) + 1
            p += 1
        else:
            px += b
            p += b
        if px > w:
            return None
    return p - start


for fi in (0, 2, 8, 10, 12, 14, 16, 19, 21, 23):
    base = 6 + fi * 8
    w, h = d[base + 2], d[base + 3]
    off = int.from_bytes(d[base + 4:base + 8], "little")
    lo = [int.from_bytes(d[off + i * 2:off + i * 2 + 2], "little") for i in range(h)]
    ok0 = ok2 = 0
    for i in range(1, h):
        delta = lo[i + 1] - lo[i] if i + 1 < h else None
        c = decode_px(off + lo[i], w)
        if c is not None and (delta is None or c == delta):
            ok0 += 1
        c2 = decode_px(off + lo[i] - 2, w)
        if c2 is not None and (delta is None or c2 == delta):
            ok2 += 1
    print("frame %3d (w=%d h=%d off=%d): rows1+ at lo[i]: %d/%d   at lo[i]-2: %d/%d"
          % (fi, w, h, off, ok0, h - 1, ok2, h - 1))

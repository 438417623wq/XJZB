"""Classify all 229 marine frames by which line-offset base validates."""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")
fc = int.from_bytes(d[0:2], "little")


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


n_off = n_off2 = n_amb = 0
for fi in range(fc):
    base = 6 + fi * 8
    w, h = d[base + 2], d[base + 3]
    off = int.from_bytes(d[base + 4:base + 8], "little")
    lo = [int.from_bytes(d[off + i * 2:off + i * 2 + 2], "little") for i in range(h)]
    s0 = s2 = 0
    for i in range(1, h):
        delta = lo[i + 1] - lo[i] if i + 1 < h else None
        c = decode_px(off + lo[i], w)
        if c is not None and (delta is None or c == delta):
            s0 += 1
        c2 = decode_px(off + lo[i] - 2, w)
        if c2 is not None and (delta is None or c2 == delta):
            s2 += 1
    m = h - 1
    if s0 >= m - 2 and s0 > s2:
        n_off += 1
        tag = "OFF "
    elif s2 >= m - 2 and s2 > s0:
        n_off2 += 1
        tag = "OFF2"
    else:
        n_amb += 1
        tag = "??? "
    if fi < 40 or tag == "??? ":
        print("%s f%03d off=%5d %s score off=%2d off2=%2d (m=%d)" % (tag, fi, off, "pair:" + ("A" if fi % 2 == 0 else "B"), s0, s2, m))
print("totals: OFF=%d OFF2=%d ambiguous=%d" % (n_off, n_off2, n_amb))

"""Scan frame 10's region for row-start positions consistent with deltas."""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")

W = 24
lo = [50, 61, 75, 90, 106, 121, 140, 161, 185, 211, 235, 257, 276, 294, 310, 325, 338, 351, 365, 381, 397, 414, 422, 434, 446]
off = 4044


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


for i in range(len(lo) - 1):
    delta = lo[i + 1] - lo[i]
    hits = []
    base = off + lo[i] - 6
    for dp in range(-6, delta + 8):
        p = off + lo[i] + dp
        c = decode_px(p, W)
        if c == delta:
            hits.append(dp)
    print("row %2d delta=%2d  row-start relative hits: %s" % (i, delta, hits))

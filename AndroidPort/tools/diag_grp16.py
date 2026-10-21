"""Exhaustive decode attempt over frame 10's region; print every exact-24px decode."""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")

W = 24
lo = [50, 61, 75, 90, 106, 121, 140, 161, 185, 211, 235, 257, 276, 294, 310, 325, 338, 351, 365, 381, 397, 414, 422, 434, 446]
off = 4044


def decode_px(p, w):
    px = 0
    start = p
    ops = []
    while px < w:
        if p >= len(d):
            return None, None
        b = d[p]
        p += 1
        if b & 0x80:
            ops.append("s%d" % (b & 0x7F))
            px += b & 0x7F
        elif b & 0x40:
            ops.append("r%d" % ((b & 0x3F) + 1))
            p += 1
            px += (b & 0x3F) + 1
        else:
            ops.append("c%d" % b)
            px += b
            p += b
        if px > w:
            return None, None
    return p - start, ops


print("=== decodes to exactly 24px in frame 10 region (start, consumed, ops) ===")
for p in range(off + 44, off + 460):
    c, ops = decode_px(p, W)
    if c is not None and 3 <= c <= 30:
        rel = p - off
        # which row region does this start in?
        row = max(i for i in range(len(lo)) if lo[i] <= rel) if rel >= lo[0] else -1
        print("start=off+%3d (lo=%3d) consumed=%2d ops=%s" % (rel, lo[row] if row >= 0 else -1, c, " ".join(ops)))

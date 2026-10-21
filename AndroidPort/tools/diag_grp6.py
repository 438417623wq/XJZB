"""Brute-force RLE op variants until marine frame 0 decodes cleanly."""
import struct
import sc_archive
from pkware import Bits  # not used; local bit reader below

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")
fc, mw, mh = int.from_bytes(d[0:2], "little"), int.from_bytes(d[2:4], "little"), int.from_bytes(d[4:6], "little")
xoff, yoff, w, h = d[6], d[7], d[8], d[9]
off = int.from_bytes(d[10:14], "little")
print("frame0: xoff=%d yoff=%d w=%d h=%d off=%d" % (xoff, yoff, w, h, off))
line_offs = [int.from_bytes(d[off + i * 2:off + i * 2 + 2], "little") for i in range(h)]
print("line_offs[:10]:", line_offs[:10], "deltas:", [line_offs[i + 1] - line_offs[i] for i in range(min(9, h - 1))])


def try_row(p, skip_adj, run_adj, copy_adj, w):
    """Decode one row; return (pixels, endpos) or None."""
    px = []
    while len(px) < w:
        if p >= len(d):
            return None
        b = d[p]
        p += 1
        if b & 0x80:
            cnt = (b & 0x7F) + skip_adj
            px.extend([255] * cnt)
        elif b & 0x40:
            cnt = (b & 0x3F) + run_adj
            if p >= len(d):
                return None
            c = d[p]
            p += 1
            px.extend([c] * cnt)
        else:
            cnt = b + copy_adj
            if p + cnt > len(d):
                return None
            px.extend(d[p:p + cnt])
            p += cnt
    if len(px) != w:
        return None
    return px, p


import itertools
for skip_adj, run_adj, copy_adj in itertools.product((0, 1), (0, 1), (0, 1)):
    ok_rows = 0
    endpos = None
    for row in range(min(h, 6)):
        r = try_row(off + line_offs[row], skip_adj, run_adj, copy_adj, w)
        if r is None:
            break
        ok_rows += 1
        endpos = r[1]
    print("skip+%d run+%d copy+%d -> %d/6 rows ok" % (skip_adj, run_adj, copy_adj, ok_rows))

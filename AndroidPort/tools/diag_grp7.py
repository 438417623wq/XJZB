import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")
h, w = d[9], d[8]
off = int.from_bytes(d[10:14], "little")
line_offs = [int.from_bytes(d[off + i * 2:off + i * 2 + 2], "little") for i in range(h)]


def decode_row(p, run_adj, w):
    px = []
    start = p
    while len(px) < w:
        b = d[p]
        p += 1
        if b & 0x80:
            px.extend([255] * (b & 0x7F))
        elif b & 0x40:
            cnt = (b & 0x3F) + run_adj
            c = d[p]
            p += 1
            px.extend([c] * cnt)
        else:
            px.extend(d[p:p + b])
            p += b
    return len(px) == w, p - start


for run_adj in (0, 1):
    ok = 0
    for row in range(h):
        p = off + line_offs[row]
        good, used = decode_row(p, run_adj, w)
        expect = (line_offs[row + 1] - line_offs[row]) if row < h - 1 else None
        if good and (expect is None or used == expect):
            ok += 1
        elif row < 8:
            print("run+%d row %d: used=%d expected=%s good=%s" % (run_adj, row, used, expect, good))
    print("run_adj=%d: %d/%d rows consistent" % (run_adj, ok, h))

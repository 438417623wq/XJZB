"""Diagnose SCV frame 12 rows across shifts."""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\SCV.grp")
print("total size:", len(d))

fi = 12
base = 6 + fi * 8
x, y, w, h = d[base], d[base + 1], d[base + 2], d[base + 3]
off = int.from_bytes(d[base + 4:base + 8], "little")
print("f12 box=(%d,%d) %dx%d off=%d" % (x, y, w, h, off))
lo = [int.from_bytes(d[off + i * 2:off + i * 2 + 2], "little") for i in range(h)]
print("lo:", lo)
print("deltas:", [lo[i + 1] - lo[i] for i in range(h - 1)])


def decode_row(p, w):
    px = 0
    ops = []
    start = p
    while px < w:
        if p >= len(d):
            return None, None, ops
        b = d[p]
        p += 1
        if b & 0x80:
            ops.append("s%d" % (b & 0x7F))
            px += b & 0x7F
        elif b & 0x40:
            if p >= len(d):
                return None, None, ops
            ops.append("r%d" % (b & 0x3F))
            p += 1
            px += b & 0x3F
        else:
            ops.append("c%d" % b)
            px += b
            p += b
        if px > w:
            return None, None, ops
    return px, p - start, ops


for shift in (0, -2, -4, 2):
    okc = 0
    samples = []
    for i in range(1, min(h, 10)):
        r = decode_row(off + lo[i] + shift, w)
        delta = lo[i + 1] - lo[i]
        if r[0] is not None and r[1] == delta:
            okc += 1
        elif i < 5:
            samples.append((i, r[1], delta, r[2]))
    print("shift %+d: %d/9 delta-exact; samples:" % (shift, okc), samples[:3])

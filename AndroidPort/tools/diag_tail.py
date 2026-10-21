"""Validate the LAST frame: does its data end exactly at EOF with delta-exact rows?"""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")
N = len(d)
print("file length:", N)

fc = int.from_bytes(d[0:2], "little")
for fi in (fc - 1, fc - 2, 17, 100, 150, 200):
    base = 6 + fi * 8
    x, y, w, h = d[base], d[base + 1], d[base + 2], d[base + 3]
    off = int.from_bytes(d[base + 4:base + 8], "little")
    if off + 2 * h > N:
        print("f%03d: table beyond EOF" % fi)
        continue
    lo = [int.from_bytes(d[off + i * 2:off + i * 2 + 2], "little") for i in range(h)]


    def decode_row(p, w):
        px = 0
        start = p
        while px < w:
            if p >= N:
                return None
            b = d[p]
            p += 1
            if b & 0x80:
                px += b & 0x7F
            elif b & 0x40:
                px += b & 0x3F
                p += 1
            else:
                px += b
                p += b
            if px > w:
                return None
        return p - start


    for shift in range(-4, 5):
        ok = 0
        for i in range(1, h):
            r = decode_row(off + lo[i] + shift, w)
            delta = lo[i + 1] - lo[i] if i + 1 < h else None
            if r is not None and (delta is None or r == delta):
                ok += 1
        if ok >= h - 3:
            # last row end position at this shift
            last_end = off + lo[h - 1] + shift
            r = decode_row(last_end, w)
            print("f%03d (off=%d w=%d h=%d): shift=%+d rows %d/%d delta-exact; last row start=%d end=%s (EOF=%d)"
                  % (fi, off, w, h, shift, ok, h - 1, last_end, (last_end + r) if r else "?", N))

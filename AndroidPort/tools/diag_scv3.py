"""Scan table-base and row-base configs for SCV f12."""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\SCV.grp")

fi = 12
base = 6 + fi * 8
w, h = d[base + 2], d[base + 3]
off = int.from_bytes(d[base + 4:base + 8], "little")


def decode_row(p, w):
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
            px += b & 0x3F
            p += 1
        else:
            px += b
            p += b
        if px > w:
            return None
    return p - start


for tb in (off - 1, off, off + 1):
    lo = [int.from_bytes(d[tb + i * 2:tb + i * 2 + 2], "little") for i in range(h)]
    mono = all(lo[i] <= lo[i + 1] for i in range(h - 1))
    for rb in (-2, -1, 0, 1, 2):
        ok = 0
        for i in range(1, h):
            r = decode_row(tb + lo[i] + rb, w)
            delta = lo[i + 1] - lo[i] if i + 1 < h else None
            if r is not None and (delta is None or r == delta):
                ok += 1
        if ok > h // 3:
            print("table@%+d rowadj%+d: %d/%d delta-exact (mono=%s, lo[0]=%d)"
                  % (tb - off, rb, ok, h - 1, mono, lo[0]))

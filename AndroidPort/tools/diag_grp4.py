"""Verify the 8-byte GRP table entry hypothesis: {4 info bytes, u32 offset}."""
import struct
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")


def decode_frame(data, p, mw, mh):
    """Standard GRP RLE for one frame; returns pixels or raises."""
    px = bytearray([255]) * (mw * mh)
    for y in range(mh):
        x = 0
        while True:
            b = data[p]
            p += 1
            if b == 0x80:
                break
            if b & 0x80:
                count = ((b & 0x3F) << 8) | data[p]
                p += 1
                if b & 0x40:
                    x += count
                else:
                    c = data[p]
                    p += 1
                    for k in range(count):
                        if x + k < mw:
                            px[y * mw + x + k] = c
                    x += count
            else:
                count = b & 0x3F
                if b & 0x40:
                    x += count
                else:
                    c = data[p]
                    p += 1
                    for k in range(count):
                        if x + k < mw:
                            px[y * mw + x + k] = c
                    x += count
            if x > mw + 4:
                raise ValueError("row overflow x=%d" % x)
    return px, p


for n in ["unit\\terran\\marine.grp", "unit\\protoss\\dragoon.grp", "unit\\zerg\\zergling.grp"]:
    d = SD.read(n)
    fc, mw, mh = struct.unpack_from("<HHH", d, 0)
    print("%s fc=%d %dx%d" % (n, fc, mw, mh))
    info0 = d[6:10]
    off0 = struct.unpack_from("<I", d, 10)[0]
    exp = 6 + fc * 8
    print("  entry0 info=%s off=%d (6+8*fc=%d)" % (info0.hex(), off0, exp))
    try:
        px, end = decode_frame(d, off0, mw, mh)
        drawn = sum(1 for v in px if v != 255)
        print("  frame0 OK: %d/%d pixels drawn, ends at %d (next off?)"
              % (drawn, mw * mh, end))
    except Exception as e:
        print("  frame0 FAIL:", e)

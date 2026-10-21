"""Try multiple frame-data layout hypotheses for the extended GRP format."""
import struct
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")


def try_decode(data, p, w, h, label):
    """Standard RLE ops into a w*h canvas; returns (pixels, consumed) or None."""
    px = bytearray([255]) * (w * h)
    p0 = p
    try:
        for y in range(h):
            x = 0
            while True:
                b = data[p]
                p += 1
                if b == 0x80:
                    break
                if b & 0x80:
                    count = ((b & 0x3F) << 8) | data[p]
                    p += 1
                    if not (b & 0x40):
                        c = data[p]
                        p += 1
                        for k in range(count):
                            if x + k < w:
                                px[y * w + x + k] = c
                    x += count
                else:
                    count = b & 0x3F
                    if b & 0x40:
                        x += count
                    else:
                        c = data[p]
                        p += 1
                        for k in range(count):
                            if x + k < w:
                                px[y * w + x + k] = c
                        x += count
                if x > w + 4:
                    return None
        return px, p - p0
    except IndexError:
        return None


n = "unit\\terran\\marine.grp"
d = SD.read(n)
fc, mw, mh = struct.unpack_from("<HHH", d, 0)
info = d[6:10]
off0 = struct.unpack_from("<I", d, 10)[0]
print("fc=%d canvas=%dx%d info=%s off0=%d" % (fc, mw, mh, info.hex(), off0))

# hypothesis A: compact frame w x h from info bytes, at off0
for order, (w, h) in {
    "w,h = info[0],info[1]": (info[0], info[1]),
    "w,h = info[2],info[3]": (info[2], info[3]),
    "w,h = info[1],info[0]": (info[1], info[0]),
}.items():
    r = try_decode(d, off0, w, h, order)
    print("A compact %-22s -> %s" % (order, "OK consumed=%d" % r[1] if r else "fail"))

# hypothesis B: full canvas but data starts with 4-byte prefix
for skip in (0, 2, 4):
    r = try_decode(d, off0 + skip, mw, mh, "skip%d" % skip)
    print("B full canvas skip=%d -> %s" % (skip, "OK consumed=%d" % r[1] if r else "fail"))

# hypothesis C: maybe offsets are the FIRST u32 (entries at 6+8i) and info second
off_alt = struct.unpack_from("<I", d, 6)[0]
print("C offset-first value:", off_alt, "- implausible" if off_alt > len(d) else "")

# hypothesis D: table is standard u32[fc] but frames start after a 4-byte gap:
# check whether entry u32s at 6+4i+4 pattern continue increasing
vals = struct.unpack_from("<12I", d, 6)
print("D first 12 u32s:", [v for v in vals])

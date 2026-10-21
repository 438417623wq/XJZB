"""Diagnose the GRP structure of marine.grp."""
import struct
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
data = SD.read("unit\\terran\\marine.grp")
print("size:", len(data))
fc, mw, mh = struct.unpack_from("<HHH", data, 0)
print("frames=%d w=%d h=%d" % (fc, mw, mh))
offs = struct.unpack_from("<%dI" % fc, data, 6)
print("offsets[0:8]:", offs[:8])
print("table end:", 6 + fc * 4, "offset[0] rel to data start:", offs[0] - (6 + fc * 4))

# trace frame 0 rows
p = offs[0]
for row in range(8):
    start = p
    x = 0
    while True:
        if p >= len(data):
            print("EOF at row", row, "pos", p)
            break
        b = data[p]
        p += 1
        if b == 0x80:
            print("row %d: %d bytes, ops ok" % (row, p - start))
            break
        if b & 0x80:
            count = ((b & 0x3F) << 8) | data[p]
            p += 1
            if not (b & 0x40):
                p += 1
            x += count
        else:
            count = b & 0x3F
            if b & 0x40:
                x += count
            else:
                p += 1
                x += count
        if x > mw + 8:
            print("row %d OVERFLOW x=%d > w=%d (stopping trace)" % (row, x, mw))
            break
    if p >= len(data) or x > mw + 8:
        break

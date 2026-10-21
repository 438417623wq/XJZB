"""Scan the whole GRP for positions where frame-10-like rows decode consistently."""
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
d = SD.read("unit\\terran\\marine.grp")

W = 24
CONSUME = 11


def decode_px(p, w, limit=None):
    """Decode with wiki ops; return (pixels, consumed) or None."""
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
            cnt = b & 0x3F
            p += 1
            px += cnt
        else:
            px += b
            p += b
        if limit and p - start > limit:
            return None
        if px > w:
            return None
    return px, p - start


# find offsets p where a 24-pixel row consumes exactly 11 bytes
hits = []
for p in range(1500, len(d) - 40):
    r = decode_px(p, W, CONSUME + 2)
    if r and r[1] == CONSUME:
        hits.append(p)
print("exact hits (24px, 11B):", len(hits), hits[:20])

# context around the first hit
if hits:
    p0 = hits[0]
    print("context:", d[p0 - 4:p0].hex(), "|", d[p0:p0 + CONSUME].hex(), "|", d[p0 + CONSUME:p0 + CONSUME + 4].hex())

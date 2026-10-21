"""StarCraft GRP sprite decoder (gap-aware, validated against marine/zerg/etc).

Layout:
    u16 frameCount, u16 maxWidth, u16 maxHeight
    frame headers, 8 bytes each: {u8 x, u8 y, u8 w, u8 h, u32 dataOffset}
    at dataOffset: u16 lineOffsets[h], entry 0 == 2*h (table size)
    row ops (stop as soon as x >= w; over-encoded rows simply stop):
        b & 0x80 -> skip (b & 0x7F) transparent pixels
        b & 0x40 -> run of (b & 0x3F) pixels of the next palette index
        else     -> copy (b) literal palette indices

All reads go through gapio.GapReader so the repack's missing bytes only cost
a few pixels instead of shifting the whole file.
"""
from gapio import GapReader


def decode_grp(data, gaps=()):
    g = GapReader(data, gaps)
    fc = g.u16(0)
    mw = g.u16(2)
    mh = g.u16(4)
    frames = []
    for fi in range(fc):
        base = 6 + fi * 8
        xoff = g.byte(base)
        yoff = g.byte(base + 1)
        w = g.byte(base + 2)
        h = g.byte(base + 3)
        off = g.u32(base + 4)
        if w == 0 or h == 0:
            frames.append({"x": xoff, "y": yoff, "w": 1, "h": 1, "px": bytearray([255])})
            continue
        px = bytearray([255]) * (w * h)
        for row in range(h):
            p = off + g.u16(off + row * 2)
            x = 0
            guard = 0
            while x < w and guard < 4096:
                guard += 1
                b = g.byte(p)
                p += 1
                if b & 0x80:
                    x += b & 0x7F
                elif b & 0x40:
                    c = g.byte(p)
                    p += 1
                    cnt = b & 0x3F
                    for k in range(cnt):
                        if x + k < w:
                            px[row * w + x + k] = c
                    x += cnt
                else:
                    cnt = b
                    if cnt == 0:
                        continue
                    for k in range(cnt):
                        if x + k < w:
                            px[row * w + x + k] = g.byte(p + k)
                    p += cnt
                    x += cnt
        frames.append({"x": xoff, "y": yoff, "w": w, "h": h, "px": px})
    return frames, mw, mh

"""Test the per-row-offset-table GRP variant.

Hypothesis: a frame's data begins with `h` little-endian 16-bit row offsets
(relative to the frame start), and each row's bytes are pure pixel RLE with NO
line-type byte:
    0x80 | n -> skip n transparent pixels
    n        -> copy n+1 palette indices
Rows sharing an offset are duplicates (the previous row); offsets equal to the
stream end mean a fully transparent row.

Compares several base interpretations and renders zoomed PNGs for inspection.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\extracted"


def pal_ramp():
    p = [(0, 0, 0, 0)]
    for i in range(1, 256):
        p.append((i, (i * 5) % 256, 255 - i, 255))
    return p


def read_row(d, p, W, pal, px, row, x0):
    """Decode one row of pixel RLE. Returns the end offset."""
    col = 0
    while col < W and p < len(d):
        c = d[p]
        p += 1
        if c & 0x80:
            col += c & 0x7F
        else:
            for _ in range(c + 1):
                if col >= W or p >= len(d):
                    break
                px[x0 + col, row] = pal[d[p]]
                p += 1
                col += 1
    return p


def render(d, fr, pal, base_mode):
    x, y, W, H, off = fr
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()

    if off + H * 2 > len(d):
        return None, None
    table = [struct.unpack_from("<H", d, off + i * 2)[0] for i in range(H)]

    if base_mode == "frame":
        base = off
    elif base_mode == "aftertable":
        base = off + H * 2
    elif base_mode == "aftertable_minus2":
        base = off + H * 2 - 2
    else:
        base = off

    for i in range(H):
        p = base + table[i]
        if p >= len(d):
            continue
        read_row(d, p, W, pal, px, i, 0)
    return img, table


def main():
    os.makedirs(OUT, exist_ok=True)
    pal = pal_ramp()
    with Archive(os.path.join(ROOT, "StarDat.mpq")) as a:
        for fname in ("unit\\protoss\\dragoon.grp", "unit\\terran\\tank.grp"):
            d = a.read(fname)
            frames, sw, sh = struct.unpack_from("<HHH", d, 0)
            fr = struct.unpack_from("<BBBBI", d, 6)
            x, y, fw, fh, off = fr
            # NOTE: the frame header stores the dimensions directly -- there is
            # no "-1" bias. Using fw+1/fh+1 mis-sizes the row-offset table.
            W, H = fw, fh
            print("== %s frames=%d sheet=%dx%d  frame0 %dx%d off=%d"
                  % (fname, frames, sw, sh, W, H, off))
            print("   bytes at off: %s" % d[off:off + 24].hex(" "))
            table = [struct.unpack_from("<H", d, off + i * 2)[0] for i in range(H)]
            print("   H*2=%d  table[0]=%d  (should match)" % (H * 2, table[0]))
            for mode in ("frame", "aftertable"):
                img, _t = render(d, (x, y, W, H, off), pal, mode)
                if img is None:
                    continue
                nz = sum(1 for q in list(img.getdata()) if q[3])
                tag = fname.split("\\")[-1].replace(".grp", "")
                path = os.path.join(OUT, "%s_%s.png" % (tag, mode))
                img.resize((W * 5, H * 5), Image.NEAREST).save(path)
                print("   mode=%-11s opaque_px=%-6d -> %s" % (mode, nz, os.path.basename(path)))
            print()


if __name__ == "__main__":
    main()

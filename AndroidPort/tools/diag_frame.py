"""Render one dragoon frame at high zoom with a debug ramp palette.

Separates silhouette correctness from palette correctness: if the shape is a
dragoon, the RLE walk is right and only the palette is wrong.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\extracted"


def debug_pal():
    # index 0 transparent-ish; others spread across a visible ramp
    p = [(0, 0, 0, 0)]
    for i in range(1, 256):
        p.append((i, (i * 7) % 256, 255 - i, 255))
    return p


def walk(d, fr, W, H):
    """Return the RLE op list for one frame, for inspection."""
    x, y, w, h, off = fr
    ops = []
    p = off
    row = 0
    while row < h and p < len(d):
        lt = d[p]
        p += 1
        if lt == 0:
            n = d[p]
            p += 1
            ops.append(("skip", row, n))
            row += n
        elif lt == 2:
            ops.append(("dup", row, 0))
            row += 1
        else:
            col = 0
            segs = []
            while col < w and p < len(d):
                c = d[p]
                p += 1
                if c & 0x80:
                    segs.append(("t", c & 0x7F))
                    col += c & 0x7F
                else:
                    segs.append(("l", c + 1))
                    p += c + 1
                    col += c + 1
            ops.append(("row", row, segs))
            row += 1
    return ops


def render(d, fr, pal):
    x, y, w, h, off = fr
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    p = off
    row = 0
    prev = None
    while row < h and p < len(d):
        lt = d[p]
        p += 1
        if lt == 0:
            row += d[p]
            p += 1
            prev = None
        elif lt == 2:
            if prev:
                for i in range(w):
                    px[i, row] = prev[i]
            row += 1
        else:
            cur = [(0, 0, 0, 0)] * w
            col = 0
            while col < w and p < len(d):
                c = d[p]
                p += 1
                if c & 0x80:
                    col += c & 0x7F
                else:
                    for _ in range(c + 1):
                        if p >= len(d) or col >= w:
                            break
                        cur[col] = pal[d[p]]
                        p += 1
                        col += 1
            for i in range(w):
                px[i, row] = cur[i]
            prev = cur
            row += 1
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    pal = debug_pal()
    with Archive(os.path.join(ROOT, "StarDat.mpq")) as a:
        d = a.read("unit\\protoss\\dragoon.grp")
        frames, sw, sh = struct.unpack_from("<HHH", d, 0)
        print("dragoon: frames=%d sheet=%dx%d size=%d" % (frames, sw, sh, len(d)))
        fr = struct.unpack_from("<BBBBI", d, 6)
        x, y, fw, fh, off = fr
        W, H = fw + 1, fh + 1
        print("frame0: x=%d y=%d W=%d H=%d off=%d" % (x, y, W, H, off))
        ops = walk(d, (x, y, W, H, off), W, H)
        print("ops (%d):" % len(ops))
        for o in ops[:14]:
            print("   ", o)
        img = render(d, (x, y, W, H, off), pal)
        img.resize((W * 6, H * 6), Image.NEAREST).save(os.path.join(OUT, "dragoon_f0_zoom.png"))
        print("wrote dragoon_f0_zoom.png")


if __name__ == "__main__":
    main()

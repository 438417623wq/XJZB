"""Classic sequential GRP RLE decoder, with correct frame dimensions.

Earlier attempts used fw+1 / fh+1 for the frame size. Reading one pixel and one
row too many desynchronises the RLE stream. This tests the classic algorithm
with the header dimensions taken literally.
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


def decode(d, fr, W, H, pal):
    x, y, _fw, _fh, off = fr
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    p = off
    row = 0
    prev = None
    while row < H:
        if p >= len(d):
            break
        lt = d[p]
        p += 1
        if lt == 0:                     # skip rows
            if p >= len(d):
                break
            row += d[p]
            p += 1
            prev = None
        elif lt == 2:                   # duplicate previous row
            if prev:
                for i in range(W):
                    px[i, row] = prev[i]
            row += 1
        else:                           # RLE row
            cur = [(0, 0, 0, 0)] * W
            col = 0
            while col < W:
                if p >= len(d):
                    break
                c = d[p]
                p += 1
                if c & 0x80:
                    col += c & 0x7F
                else:
                    for _ in range(c + 1):
                        if col >= W or p >= len(d):
                            break
                        cur[col] = pal[d[p]]
                        p += 1
                        col += 1
            for i in range(W):
                px[i, row] = cur[i]
            prev = cur
            row += 1
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    pal = pal_ramp()
    with Archive(os.path.join(ROOT, "StarDat.mpq")) as a:
        for fname in ("unit\\protoss\\dragoon.grp", "unit\\terran\\tank.grp",
                      "unit\\zerg\\zulShad.grp"):
            d = a.read(fname)
            frames, sw, sh = struct.unpack_from("<HHH", d, 0)
            x, y, fw, fh, off = struct.unpack_from("<BBBBI", d, 6)
            tag = fname.split("\\")[-1].replace(".grp", "")
            for label, W, H in (("exact", fw, fh), ("plus1", fw + 1, fh + 1)):
                img = decode(d, (x, y, fw, fh, off), W, H, pal)
                nz = sum(1 for q in list(img.get_flattened_data()) if q[3]) \
                    if hasattr(img, "get_flattened_data") else \
                    sum(1 for q in list(img.getdata()) if q[3])
                path = os.path.join(OUT, "cls_%s_%s.png" % (tag, label))
                img.resize((W * 5, H * 5), Image.NEAREST).save(path)
                print("%-28s %-6s W=%-3d H=%-3d opaque=%-5d -> %s"
                      % (fname, label, W, H, nz, os.path.basename(path)))
            print()


if __name__ == "__main__":
    main()

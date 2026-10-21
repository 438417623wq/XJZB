"""Score GRP decode variants by silhouette smoothness.

A correctly decoded sprite has a compact, connected silhouette: the leftmost
and rightmost opaque pixels vary smoothly from row to row. Noise-like decodes
jitter wildly. Use that as an automatic oracle instead of eyeballing.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\extracted"


def real_pal():
    pb = open(r"F:\KF\XJZB\AndroidPort\assets_src\palettes\units.pal", "rb").read()
    return [tuple(pb[i * 3:i * 3 + 3]) + (255,) for i in range(256)]


def decode_offtable(d, W, H, off, pal, reverse=False, colstep=0):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    table = [struct.unpack_from("<H", d, off + i * 2)[0] for i in range(H)]
    bounds = table + [table[-1] + 600]
    order = list(range(H))
    if reverse:
        order = order[::-1]
    for pos, i in enumerate(order):
        p = off + table[i]
        end = off + bounds[i + 1]
        col = 0
        while col < W and p < end and p < len(d):
            c = d[p]
            p += 1
            if c & 0x80:
                col += c & 0x7F
            else:
                for _ in range(c + 1):
                    if col >= W or p >= len(d):
                        break
                    px[col, i] = pal[d[p]]
                    p += 1
                    col += 1
    return img


def silhouette_score(img):
    """Lower is smoother: sum of |left(i)-left(i-1)| + |right(i)-right(i-1)|."""
    W, H = img.size
    px = img.load()
    lefts, rights = [], []
    for y in range(H):
        xs = [x for x in range(W) if px[x, y][3]]
        if xs:
            lefts.append(min(xs))
            rights.append(max(xs))
    if len(lefts) < 3:
        return float("inf")
    s = 0
    for i in range(1, len(lefts)):
        s += abs(lefts[i] - lefts[i - 1]) + abs(rights[i] - rights[i - 1])
    return s / len(lefts)


def main():
    pal = real_pal()
    with Archive(os.path.join(ROOT, "StarDat.mpq")) as a:
        for fn in ("unit\\protoss\\dragoon.grp", "unit\\terran\\tank.grp"):
            d = a.read(fn)
            frames, sw, sh = struct.unpack_from("<HHH", d, 0)
            x, y, fw, fh, off = struct.unpack_from("<BBBBI", d, 6)
            print("== %s  W=%d H=%d off=%d" % (fn, fw, fh, off))
            # also compare: sequential classic over the same frame span
            for label, rev in (("forward", False), ("reversed", True)):
                img = decode_offtable(d, fw, fh, off, pal, reverse=rev)
                sc = silhouette_score(img)
                nz = sum(1 for q in list(img.getdata()) if q[3])
                print("   offtable %-9s score=%-8.2f opaque=%d" % (label, sc, nz))
                img.resize((fw * 5, fh * 5), Image.NEAREST).save(
                    os.path.join(OUT, "score_%s_%s.png"
                                 % (fn.split("\\")[-1].replace(".grp", ""), label)))
            print()


if __name__ == "__main__":
    main()

"""Test the row-offset-table hypothesis for these GRP variants.

Frame data appears to begin with one 16-bit offset per row (H entries,
increasing), followed by the RLE streams those offsets point at. Decode each
row independently and render a PNG to check it looks like a unit.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\extracted"


def gray():
    return [(i, i, i, 255) for i in range(256)]


def decode_row(d, p, W, pal, px, row, ox):
    """Decode one RLE row starting at absolute offset p. Returns new p."""
    lt = d[p]
    p += 1
    if lt == 0:
        return p
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
                px[ox + col, row] = pal[d[p]]
                p += 1
                col += 1
    return p


def try_variant(d, frame, pal, mode):
    x, y, W, H, off = frame
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    table = []
    for i in range(H):
        if off + i * 2 + 1 >= len(d):
            return None
        table.append(struct.unpack_from("<H", d, off + i * 2)[0])

    if mode == "rows":
        # offsets are absolute-ish; try relative to frame start
        for i in range(H):
            p = off + table[i]
            if p >= len(d):
                continue
            decode_row(d, p, W, pal, px, i, 0)
    elif mode == "rows_seq":
        # offsets point into a shared stream; read sequentially
        p = off + table[0]
        for i in range(H):
            if p >= len(d):
                break
            p = decode_row(d, p, W, pal, px, i, 0)
    return img, table


def main():
    os.makedirs(OUT, exist_ok=True)
    pal = gray()
    with Archive(os.path.join(ROOT, "BrooDat.mpq")) as a:
        for fname in ("unit\\terran\\medic.grp", "unit\\zerg\\Zlurker.grp"):
            d = a.read(fname)
            frames, sw, sh = struct.unpack_from("<HHH", d, 0)
            x, y, fw, fh, off = struct.unpack_from("<BBBBI", d, 6)
            W, H = fw + 1, fh + 1
            print("== %s W=%d H=%d off=%d" % (fname, W, H, off))
            table = [struct.unpack_from("<H", d, off + i * 2)[0] for i in range(H)]
            print("   row table (%d): %s" % (H, table[:10]))
            print("   last entries  : %s" % table[-5:])
            print("   at off+table[0]=%d: %s" % (off + table[0], d[off + table[0]:off + table[0] + 16].hex(" ")))
            print("   at off+%d (table end): %s" % (H * 2, d[off + H * 2:off + H * 2 + 16].hex(" ")))

            for mode in ("rows", "rows_seq"):
                r = try_variant(d, (x, y, W, H, off), pal, mode)
                if not r:
                    continue
                img, _t = r
                nz = sum(1 for p in img.getdata() if p[3])
                print("   mode=%-9s non-empty px=%d" % (mode, nz))
                img.resize((W * 4, H * 4), Image.NEAREST).save(
                    os.path.join(OUT, "%s_%s.png" % (fname.split("\\")[-1].replace(".grp", ""), mode)))
            print()


if __name__ == "__main__":
    main()

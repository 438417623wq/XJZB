"""Derive the row encoding from the offset deltas.

If table[i] is the offset of row i, then row i occupies bytes
[table[i], table[i+1]). For the correct interpretation, the RLE inside each
span must consume exactly that span AND produce exactly W pixels.

Also tests the alternative that each span holds a literal indexed bitmap.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"


def walk_row(d, p, end, W):
    """RLE-walk within [p, end); return (pixels_emitted, end_offset)."""
    col = 0
    while col < W and p < end:
        c = d[p]
        p += 1
        if c & 0x80:
            col += c & 0x7F
        else:
            p += c + 1
            col += c + 1
    return col, p


def main():
    with Archive(os.path.join(ROOT, "StarDat.mpq")) as a:
        for fname in ("unit\\protoss\\dragoon.grp", "unit\\terran\\tank.grp"):
            d = a.read(fname)
            frames, sw, sh = struct.unpack_from("<HHH", d, 0)
            x, y, fw, fh, off = struct.unpack_from("<BBBBI", d, 6)
            print("== %s  frame0 fw=%d fh=%d off=%d" % (fname, fw, fh, off))

            for H, W in ((fh, fw), (fh + 1, fw + 1), (fh, fw + 1), (fh + 1, fw)):
                table = [struct.unpack_from("<H", d, off + i * 2)[0] for i in range(H)]
                if table[0] != H * 2:
                    print("   H=%-3d W=%-3d table[0]=%-5d != H*2=%d  (reject)"
                          % (H, W, table[0], H * 2))
                    continue
                print("   H=%-3d W=%-3d table[0]=%d == H*2  <== CONSISTENT" % (H, W, table[0]))
                # test RLE spans
                exact = 0
                widths = []
                for i in range(H - 1):
                    p = off + table[i]
                    end = off + table[i + 1]
                    col, pend = walk_row(d, p, end, W)
                    widths.append(col)
                    if pend == end and col == W:
                        exact += 1
                print("      rows where RLE consumes span exactly and fills W: %d/%d"
                      % (exact, H - 1))
                print("      first 10 emitted widths: %s" % widths[:10])
                span = [table[i + 1] - table[i] for i in range(min(10, H - 1))]
                print("      first 10 span lengths  : %s" % span)
            print()


if __name__ == "__main__":
    main()

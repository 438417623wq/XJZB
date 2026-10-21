"""Check whether each row's RLE ends exactly at the next row's offset.

If yes for nearly all rows, the row-offset-table layout is confirmed and only
the per-row walk needs fixing.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"


def walk(d, p, end, W):
    """RLE walk bounded by `end`; returns (col, p)."""
    col = 0
    while p < end:
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
            H, W = fh, fw
            table = [struct.unpack_from("<H", d, off + i * 2)[0] for i in range(H)]
            # append the end of the frame's data as a sentinel
            table.append(len(d) - off)

            print("== %s  W=%d H=%d off=%d  table[0]=%d" % (fname, W, H, off, table[0]))
            exact = 0
            over = 0
            under = 0
            detail = []
            for i in range(H):
                p = off + table[i]
                end = off + table[i + 1]
                col, pend = walk(d, p, end, W)
                if pend == end:
                    exact += 1
                detail.append((i, table[i + 1] - table[i], col))
            print("   rows whose walk ends exactly at the next offset: %d/%d"
                  % (exact, H))
            print("   first 12 rows (idx, span, emitted_cols):")
            for row in detail[:12]:
                print("      %s" % (row,))
            print()


if __name__ == "__main__":
    main()

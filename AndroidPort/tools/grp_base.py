"""Find the base offset that makes the row-offset table point at valid RLE rows.

Each row's data should start with a GRP line-type byte (0, 1 or 2). Scanning
the base offset is a strong, cheap constraint that pins the layout.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"


def check(d, table, base, H):
    good = 0
    for i in range(H):
        p = base + table[i]
        if 0 <= p < len(d) and d[p] in (0, 1, 2):
            good += 1
    return good


def main():
    with Archive(os.path.join(ROOT, "BrooDat.mpq")) as a:
        for fname in ("unit\\terran\\medic.grp", "unit\\zerg\\Zlurker.grp"):
            d = a.read(fname)
            frames, sw, sh = struct.unpack_from("<HHH", d, 0)
            x, y, fw, fh, off = struct.unpack_from("<BBBBI", d, 6)
            W, H = fw + 1, fh + 1
            table = [struct.unpack_from("<H", d, off + i * 2)[0] for i in range(H)]
            print("== %s H=%d off=%d" % (fname, H, off))

            best = (0, None)
            for base in range(max(0, off - 64), off + 256):
                g = check(d, table, base, H)
                if g > best[0]:
                    best = (g, base)
            print("   best base=%s valid_rows=%d/%d" % (best[1], best[0], H))

            # also try interpreting the table as offsets into the whole file
            best2 = (0, None)
            for base in range(0, min(len(d), off + 4096)):
                g = check(d, table, base, H)
                if g > best2[0]:
                    best2 = (g, base)
            print("   absolute best base=%s valid_rows=%d/%d" % (best2[1], best2[0], H))
            print()


if __name__ == "__main__":
    main()

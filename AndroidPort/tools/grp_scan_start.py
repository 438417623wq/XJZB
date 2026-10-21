"""Find the true pixel-data start for a GRP frame.

The bytes at the nominal frame offset look like an increasing word table
rather than RLE, so locate the real start empirically: try candidate offsets
and keep the one whose RLE walk stays within the frame width and fills the
frame height exactly.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"


def try_decode(d, start, W, H):
    """Walk the GRP RLE from `start`; return (ok, rows, bytes_used, maxcol)."""
    p = start
    row = 0
    maxcol = 0
    while row < H:
        if p >= len(d):
            return (False, row, p - start, maxcol)
        lt = d[p]
        p += 1
        if lt == 0:
            if p >= len(d):
                return (False, row, p - start, maxcol)
            row += d[p]
            p += 1
        elif lt == 2:
            row += 1
        else:
            col = 0
            while col < W:
                if p >= len(d):
                    return (False, row, p - start, maxcol)
                c = d[p]
                p += 1
                if c & 0x80:
                    col += c & 0x7F
                else:
                    if p + c + 1 > len(d):
                        return (False, row, p - start, maxcol)
                    p += c + 1
                    col += c + 1
            maxcol = max(maxcol, col)
            row += 1
    return (True, row, p - start, maxcol)


def main():
    with Archive(os.path.join(ROOT, "BrooDat.mpq")) as a:
        for fname in ("unit\\terran\\medic.grp", "unit\\zerg\\Zlurker.grp"):
            d = a.read(fname)
            frames, sw, sh = struct.unpack_from("<HHH", d, 0)
            print("== %s frames=%d sheet=%dx%d size=%d" % (fname, frames, sw, sh, len(d)))

            # offsets of the first few frames
            offs = []
            for i in range(min(6, frames)):
                x, y, fw, fh, off = struct.unpack_from("<BBBBI", d, 6 + i * 8)
                offs.append((x, y, fw + 1, fh + 1, off))
            print("   first frames:", offs)

            x, y, W, H, off = offs[0]
            print("   frame0 W=%d H=%d nominal_off=%d" % (W, H, off))
            print("   bytes at nominal off: %s" % d[off:off + 32].hex(" "))
            # inter-frame gap tells the frame's stored size
            if len(offs) > 1:
                print("   next frame off=%d  gap=%d" % (offs[1][4], offs[1][4] - off))

            print("   scanning candidate starts (nominal-8 .. nominal+600):")
            best = []
            lo = max(0, off - 8)
            hi = min(len(d) - 1, off + 600)
            for s in range(lo, hi):
                ok, rows, used, maxcol = try_decode(d, s, W, H)
                if ok and maxcol <= W:
                    best.append((s, used, maxcol))
            for s, used, mc in best[:10]:
                print("      start=%-6d used=%-5d maxcol=%d" % (s, used, mc))
            if not best:
                print("      no decodable start found")
            print()


if __name__ == "__main__":
    main()

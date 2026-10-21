"""Test whether StarDat.mpq holds classic RLE unit GRPs.

BrooDat's listfile gives us 903 real internal file names. Use them as keys
against StarDat's blocks and check which entries decode as classic GRPs.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"


def grp_ok(d):
    """Validate a classic RLE GRP: header sane and row walk within width."""
    if len(d) < 14:
        return None
    frames, w, h = struct.unpack_from("<HHH", d, 0)
    if not (0 < frames < 4000) or not (0 < w <= 512) or not (0 < h <= 512):
        return None
    if 6 + frames * 8 > len(d):
        return None
    x, y, fw, fh, off = struct.unpack_from("<BBBBI", d, 6)
    if off >= len(d):
        return None
    W, H = fw + 1, fh + 1
    # walk the first frame's RLE
    p = off
    row = 0
    while row < H:
        if p >= len(d):
            return None
        lt = d[p]
        p += 1
        if lt == 0:
            if p >= len(d):
                return None
            row += d[p]
            p += 1
        elif lt == 2:
            row += 1
        else:
            col = 0
            while col < W:
                if p >= len(d):
                    return None
                c = d[p]
                p += 1
                if c & 0x80:
                    col += c & 0x7F
                else:
                    p += c + 1
                    col += c + 1
            row += 1
    return (frames, w, h, W, H)


def main():
    with Archive(os.path.join(ROOT, "BrooDat.mpq")) as a:
        names = [n for n in a.read("(listfile)").decode("latin-1")
                 .replace("\r", "\n").split("\n") if n.strip()]
    print("names from BrooDat listfile: %d" % len(names))

    with Archive(os.path.join(ROOT, "StarDat.mpq")) as sd:
        present = []
        for n in names:
            bi = sd.find(n)
            if bi is not None:
                present.append((n, bi))
        print("of those, present in StarDat: %d" % len(present))

        okgrp = []
        for n, bi in present:
            if not n.lower().endswith(".grp"):
                continue
            try:
                d = sd.read_block(bi, n.split("\\")[-1])
            except Exception:
                continue
            gi = grp_ok(d)
            if gi:
                okgrp.append((n, gi, len(d)))
        print("valid classic GRPs in StarDat: %d" % len(okgrp))
        for n, gi, sz in okgrp[:25]:
            print("   %-38s frames=%-5d sheet=%dx%d frame0=%dx%d size=%d"
                  % (n, gi[0], gi[1], gi[2], gi[3], gi[4], sz))


if __name__ == "__main__":
    main()

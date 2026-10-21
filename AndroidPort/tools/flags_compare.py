"""Compare block flags between working and failing GRP entries.

If the failing entries share a distinct flag combo, the key rule differs for
them rather than the data being corrupt.
"""

import collections
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"


def grpinfo(d):
    if len(d) < 6:
        return None
    f, w, h = struct.unpack_from("<HHH", d, 0)
    if not (0 < f < 4000) or not (0 < w <= 512) or not (0 < h <= 512):
        return None
    if 6 + f * 8 > len(d):
        return None
    return (f, w, h)


def main():
    with Archive(os.path.join(ROOT, "BrooDat.mpq")) as a:
        lf = [n for n in a.read("(listfile)").decode("latin-1")
              .replace("\r", "\n").split("\n") if n.strip()]
        grps = [n for n in lf if n.lower().endswith(".grp")]

        okflags = collections.Counter()
        badflags = collections.Counter()
        pairs = []
        for n in grps:
            bi = a.find(n)
            if bi is None:
                continue
            o, cs, fs, flags, rel = a.block_table[bi]
            bare = n.split("\\")[-1]
            try:
                d = a.read_block(bi, bare)
                good = grpinfo(d) is not None
            except Exception:
                good = False
            (okflags if good else badflags)[(flags, cs == fs)] += 1
            pairs.append((n, flags, cs, fs, good))

        print("WORKING entries flag combos:")
        for k, v in okflags.most_common():
            print("   flags=0x%08X stored=%s  x%d" % (k[0], k[1], v))
        print("\nFAILING entries flag combos:")
        for k, v in badflags.most_common():
            print("   flags=0x%08X stored=%s  x%d" % (k[0], k[1], v))

        print("\nsample failing entries:")
        for n, flags, cs, fs, good in pairs:
            if not good:
                print("   %-34s flags=0x%08X cs=%-7d fs=%-7d" % (n, flags, cs, fs))
        print("\nsample working entries:")
        shown = 0
        for n, flags, cs, fs, good in pairs:
            if good and shown < 6:
                print("   %-34s flags=0x%08X cs=%-7d fs=%-7d" % (n, flags, cs, fs))
                shown += 1


if __name__ == "__main__":
    main()

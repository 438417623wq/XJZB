"""Determine which key-name form (bare vs full path) StarCraft archives use.

Earlier successes used the bare filename, but many entries still fail. Test
each candidate key-name form and count how many GRPs decode to valid sprites.
"""

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


def keyforms(name):
    parts = name.split("\\")
    bare = parts[-1]
    return {
        "full": name,
        "bare": bare,
        "full_lower": name.lower(),
        "bare_lower": bare.lower(),
        "full_nopath_lower": name.lower().replace("\\", ""),
    }


def main():
    with Archive(os.path.join(ROOT, "BrooDat.mpq")) as a:
        lf = [n for n in a.read("(listfile)").decode("latin-1")
              .replace("\r", "\n").split("\n") if n.strip()]
        grps = [n for n in lf if n.lower().endswith(".grp")]
        print("GRPs: %d" % len(grps))

        results = {}
        for mode in ("full", "bare", "full_lower", "bare_lower"):
            ok = 0
            fails = []
            for n in grps:
                bi = a.find(n)
                if bi is None:
                    continue
                try:
                    d = a.read_block(bi, keyforms(n)[mode])
                    if grpinfo(d):
                        ok += 1
                except Exception as e:
                    fails.append((n, str(e)[:40]))
            results[mode] = ok
            print("  %-12s valid=%3d  (sample fail: %s)" % (mode, ok, fails[:2]))

        # Per-file: which mode works?
        per = {}
        for n in grps:
            bi = a.find(n)
            if bi is None:
                continue
            good = []
            for mode in ("full", "bare", "full_lower", "bare_lower"):
                try:
                    if grpinfo(a.read_block(bi, keyforms(n)[mode])):
                        good.append(mode)
                except Exception:
                    pass
            per[n] = good
        both = sum(1 for v in per.values() if len(v) > 1)
        none = [n for n, v in per.items() if not v]
        print("\n  files where >1 mode works: %d" % both)
        print("  files where NO mode works: %d" % len(none))
        for n in none[:8]:
            print("     %s" % n)


if __name__ == "__main__":
    main()

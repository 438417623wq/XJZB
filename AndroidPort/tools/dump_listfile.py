"""Dump the embedded (listfile) from an MPQ archive."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def main():
    arc = sys.argv[1] if len(sys.argv) > 1 else "BrooDat.mpq"
    out = sys.argv[2] if len(sys.argv) > 2 else None
    path = os.path.join(ROOT, arc)
    with MPQ(path) as m:
        lf = m.listfile()
    print("archive=%s entries=%d" % (arc, len(lf)))
    for n in lf:
        print(n)
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lf))
        print("\nwrote %s" % out)


if __name__ == "__main__":
    main()

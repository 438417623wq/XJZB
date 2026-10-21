"""Test whether the .scm/.scx map files are readable MPQ archives.

StarCraft scenarios are MPQ archives that normally contain a single entry
'staredit\\scenario.chk' holding all terrain and unit data, unencrypted.
If these read, we get 207 real maps worth of terrain.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"
MAPDIR = os.path.join(ROOT, "maps")

CANDIDATES = [
    "staredit\\scenario.chk",
    "staredit/scenario.chk",
    "scenario.chk",
    "SCENARIO.CHK",
]


def main():
    if not os.path.isdir(MAPDIR):
        print("no maps dir")
        return
    maps = []
    for root, _dirs, files in os.walk(MAPDIR):
        for f in files:
            if f.lower().endswith((".scm", ".scx")):
                maps.append(os.path.join(root, f))
    print("map files: %d" % len(maps))

    ok = 0
    for p in maps[:12]:
        rel = os.path.relpath(p, ROOT)
        try:
            with MPQ(p) as m:
                lf = m.listfile()
                found = None
                for c in CANDIDATES:
                    if m.has(c):
                        found = c
                        break
                print("%-46s fmt=%d blocks=%-4d listfile=%-3d chk=%s"
                      % (rel, m.format_version, len(m.block_table), len(lf), found))
                if found:
                    data = m.read(found)
                    print("      chk size=%d head=%s" % (len(data), data[:16].hex(" ")))
                    ok += 1
                elif lf:
                    print("      listfile: %s" % lf[:6])
        except Exception as e:
            print("%-46s ERROR %r" % (rel, e))
    print("\nreadable scenario.chk: %d" % ok)


if __name__ == "__main__":
    main()

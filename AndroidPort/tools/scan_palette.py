"""Locate StarCraft palette files (.pal = 768 bytes = 256 RGB triples).

StarDat.mpq has no listfile, so we scan the block table for entries whose
uncompressed size is exactly 768 and test candidate palette names against them.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_archive import Archive, MPQError  # noqa: E402

ROOT = r"F:\KF\XJZB"

BASES = ["units", "tileset", "terran", "zerg", "protoss", "wirefram", "gamepal",
         "loading", "ofire", "bfire", "gfire", "green", "blue", "red", "teal",
         "title", "font", "1bit", "2bit", "3bit", "4bit", "5bit", "8bit", "neutral"]
NAMES = []
for b in BASES:
    NAMES += ["%s.pal" % b, "palette\\%s.pal" % b, "unit\\palette\\%s.pal" % b]


def main():
    path = os.path.join(ROOT, "StarDat.mpq")
    with Archive(path) as a:
        cand = [(i, e) for i, e in enumerate(a.block_table)
                if e[2] == 768 and (e[3] & 0x80000000)]
        print("blocks with uncompressed size 768: %d" % len(cand))
        for i, (o, cs, fs, flags, rel) in cand[:20]:
            print("   blk%-5d o=%-9d cs=%-6d flags=0x%08X" % (i, o, cs, flags))

        print("\ntrying palette names against each 768-byte block:")
        hits = 0
        for i, (o, cs, fs, flags, rel) in cand:
            for nm in NAMES:
                try:
                    data = a.read_block(i, nm)
                except Exception:
                    continue
                if len(data) == 768:
                    body = bytes(data)
                    # a palette should have plausible RGB values
                    mx = max(body)
                    print("   *** blk%-5d name=%-24s %d bytes max=%d head=%s"
                          % (i, nm, len(body), mx, body[:9].hex(" ")))
                    out = r"F:\KF\XJZB\AndroidPort\extracted\%s" % nm.replace("\\", "_")
                    with open(out, "wb") as fh:
                        fh.write(body)
                    hits += 1
                    break
        print("palettes recovered: %d" % hits)


if __name__ == "__main__":
    main()

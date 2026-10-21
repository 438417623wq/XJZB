"""Find palette-like data anywhere in the archives.

A StarCraft palette is 768 bytes of RGB (or 1024 with a pad byte). We scan
every entry in every archive, decompress it, and look for arrays whose values
form a plausible colour table.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"
ARCS = ["BrooDat.mpq", "StarDat.mpq", "BroodWar.mpq", "patch_rt.mpq"]


def looks_like_palette(b):
    if len(b) not in (768, 1024):
        return False
    # sample a spread of entries; a palette is not all zero / all 0xFF
    sample = [b[i] for i in range(0, len(b), 7)]
    if not sample:
        return False
    lo, hi = min(sample), max(sample)
    uniq = len(set(sample))
    return hi - lo > 40 and uniq > 6


def main():
    for arc in ARCS:
        path = os.path.join(ROOT, arc)
        if not os.path.exists(path):
            continue
        with Archive(path) as a:
            print("=== %s (%d blocks)" % (arc, len(a.block_table)))
            found = 0
            names = []
            try:
                names = [n for n in a.read("(listfile)").decode("latin-1")
                         .replace("\r", "\n").split("\n") if n.strip()]
            except Exception:
                pass
            keyname = {}
            for n in names:
                bi = a.find(n)
                if bi is not None:
                    keyname.setdefault(bi, n.split("\\")[-1])

            for i, (o, cs, fs, flags, rel) in enumerate(a.block_table):
                if fs not in (768, 1024) or not (flags & 0x80000000):
                    continue
                kn = keyname.get(i)
                if kn is None:
                    continue  # can't derive the key without the real name
                try:
                    data = a.read_block(i, kn)
                except Exception:
                    continue
                if looks_like_palette(data):
                    found += 1
                    print("   blk%-5d %-28s size=%-5d head=%s"
                          % (i, kn, len(data), data[:12].hex(" ")))
                    out = os.path.join(r"F:\KF\XJZB\AndroidPort\extracted",
                                       "pal_%s_%d.bin" % (arc.split(".")[0], i))
                    with open(out, "wb") as fh:
                        fh.write(data)
            print("   palette-like entries: %d" % found)


if __name__ == "__main__":
    main()

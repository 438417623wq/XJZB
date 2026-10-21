"""Locate the unit palette in StarDat.mpq.

StarDat has no listfile, so we test the palette key against every block and
accept candidates whose decrypted content looks like a 256-entry RGB table.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive as S  # noqa: E402
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"

NAMES = ["units.pal", "tileset.pal", "terran.pal", "zerg.pal", "protoss.pal",
         "wirefram.pal", "gamepal.pal", "loading.pal", "ofire.pal", "bfire.pal",
         "gfire.pal", "green.pal", "blue.pal", "red.pal", "teal.pal", "title.pal",
         "font.pal", "units", "tileset"]


def plausible(b):
    if len(b) < 768:
        return False
    body = b[:768]
    sample = [body[i] for i in range(0, 768, 5)]
    return (max(sample) - min(sample)) > 60 and len(set(sample)) > 8


def main():
    with Archive(os.path.join(ROOT, "StarDat.mpq")) as a:
        print("scanning %d blocks" % len(a.block_table))
        for nm in NAMES:
            base = S.hash_string(nm, S.HASH_FILE_KEY)
            for bi, (o, cs, fs, flags, rel) in enumerate(a.block_table):
                if not (flags & 0x80000000):
                    continue
                key = base
                if flags & S.FLAG_FIX_KEY:
                    key = ((base + rel) ^ fs) & 0xFFFFFFFF
                try:
                    a.fp.seek(o)
                    raw = a.fp.read(cs)
                    if flags & S.FLAG_ENCRYPTED:
                        raw = S.decrypt(raw, key)
                    if flags & S.FLAG_COMPRESS:
                        data = S.decompress_sector(raw, fs)
                    else:
                        data = raw[:fs]
                except Exception:
                    continue
                if len(data) == 768 and plausible(data):
                    print("  *** %-16s blk%-5d -> 768-byte palette!" % (nm, bi))
                    out = r"F:\KF\XJZB\AndroidPort\assets_src\palettes\%s" % nm
                    with open(out, "wb") as fh:
                        fh.write(data)
                    return
        print("no palette found by name scan")


if __name__ == "__main__":
    main()

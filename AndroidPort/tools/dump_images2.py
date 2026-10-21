"""Re-export arr/images.tbl with the current gap-aware reader.

The old images_tbl.txt was dumped before v2.5 fixed the stored-sector
detection, so the middle of the string table is garbled fragments
("rp", ".grp", ...) and the zerg building / doodad entries are unreadable.
This dump is the authoritative sprite index (719 entries, image id order).
"""
import struct

import sc_archive
from gapio import GapReader

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
BD = sc_archive.Archive(r"F:\KF\XJZB\BrooDat.mpq")


def dump_tbl(archive, name, out):
    data, gaps = archive.read_with_gaps(name)
    print("%s: %d bytes, %d gap(s) %s" % (name, len(data), len(gaps), gaps))
    g = GapReader(data, gaps)
    n = g.u16(0)
    # SC1 TBL: u16 count, then u16[count] offsets, then strings. Offsets are
    # absolute from the start of the file (see parse_images.py, which parsed
    # entries 0-364 correctly with this layout).
    offs = [g.u16(2 + i * 2) for i in range(n)]
    strs = []
    for o in offs:
        chars = bytearray()
        p = o
        for _ in range(300):
            c = g.byte(p)
            if c == 0:
                break
            chars.append(c)
            p += 1
        strs.append(chars.decode("cp1252", "replace"))
    with open(out, "w", encoding="utf8") as fp:
        for i, s in enumerate(strs):
            fp.write("%d\t%s\n" % (i, s))
    print("  entries=%d -> %s" % (n, out))
    return strs


if __name__ == "__main__":
    dump_tbl(SD, "arr\\images.tbl", "images_tbl2.txt")

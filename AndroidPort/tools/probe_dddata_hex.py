"""Hexdump the regions of badlands/jungle dddata.bin where tileset sprite-id
pairs occur, to eyeball the record structure."""
import sc_archive
from gapio import GapReader

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")


def read(name):
    d, gaps = SD.read_with_gaps(name)
    return GapReader(d, gaps)


for ts, regions in (("badlands", [(32700, 33000), (33250, 33500), (0, 120)]),
                    ("jungle", [(0, 200)]),
                    ("platform", [(0, 120)])):
    d, gaps = SD.read_with_gaps("tileset\\%s\\dddata.bin" % ts)
    g = GapReader(d, gaps)
    print("=== %s (gaps=%s) ===" % (ts, gaps))
    for lo, hi in regions:
        print("--- 0x%05x..0x%05x ---" % (lo, hi))
        for row in range(lo, hi, 16):
            bs = g.bytes_at(row, 16)
            hexs = " ".join("%02x" % b for b in bs)
            asc = "".join(chr(b) if 32 <= b < 127 else "." for b in bs)
            print("  %06x  %s  %s" % (row, hexs, asc))

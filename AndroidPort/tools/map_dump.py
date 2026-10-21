"""Deep-dump one .scm map to locate scenario.chk by its 'VER ' chunk signature.

A StarCraft CHK begins with the 4-byte chunk tag 'VER '. Searching the raw
file for that signature locates the payload independently of any decryption,
which tells us definitively whether the cipher or the table parsing is at fault.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def hexdump(data, base=0, width=16, limit=256):
    out = []
    for i in range(0, min(len(data), limit), width):
        chunk = data[i:i + width]
        hx = " ".join("%02X" % b for b in chunk)
        tx = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        out.append("      %08X  %-47s  %s" % (base + i, hx, tx))
    return "\n".join(out)


def main():
    path = os.path.join(ROOT, "maps", "(2)Bottleneck.scm")
    size = os.path.getsize(path)
    print("file: %s  size=%d" % (path, size))

    with open(path, "rb") as fp:
        blob = fp.read()

    print("\n-- header --")
    off = blob.find(b"MPQ\x1a")
    print("   MPQ magic at %d" % off)
    (magic, hsize, asize, fmt, shift, hpos, bpos, hcount, bcount) = \
        struct.unpack_from("<4sIIHHIIII", blob, off)
    print("   headerSize=%d archiveSize=%d fmt=%d sectorShift=%d (sector=%d)"
          % (hsize, asize, fmt, shift, 512 << shift))
    print("   hashPos=%d blockPos=%d hashCount=%d blockCount=%d" % (hpos, bpos, hcount, bcount))
    print("   header hex:")
    print(hexdump(blob[off:off + 64], off))

    print("\n-- search for CHK 'VER ' signature --")
    idxs = []
    start = 0
    while True:
        i = blob.find(b"VER ", start)
        if i < 0:
            break
        idxs.append(i)
        start = i + 1
    print("   occurrences: %s" % idxs[:10])
    for i in idxs[:2]:
        print("   around %d:" % i)
        print(hexdump(blob[max(0, i - 16):i + 240], max(0, i - 16)))

    with MPQ(path) as m:
        print("\n-- hash table (decrypted) --")
        for i, h in enumerate(m.hash_table[:8]):
            print("   slot%d %s" % (i, h))
        print("\n-- block table (decrypted) --")
        for i, e in enumerate(m.block_table):
            o, cs, fs, flags, rel = e
            print("   blk%d o=%-8d cs=%-8d fs=%-8d flags=0x%08X rel=%d" % (i, o, cs, fs, flags, rel))
        print("\n-- raw bytes at each block offset --")
        for i, (o, cs, fs, flags, rel) in enumerate(m.block_table):
            print("   blk%d @%d:" % (i, o))
            print(hexdump(blob[o:o + 64], o, limit=64))


if __name__ == "__main__":
    main()

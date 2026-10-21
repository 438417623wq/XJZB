"""Try every standard decompressor against a 0x08 sector.

Cheap last check: maybe the type byte does not mean PKWARE implode here.
Success criterion: output begins with 'VER ' or is exactly the sector size.
"""

import bz2
import lzma
import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def main():
    mp = os.path.join(ROOT, "maps", "(2)Bottleneck.scm")
    with MPQ(mp) as m:
        o, cs, fs, flags, rel = m.block_table[0]
        key = M.hash_string("scenario.chk", M.HASH_FILE_KEY)
        if flags & M.FLAG_FIX_KEY:
            key = ((key + rel) ^ fs) & 0xFFFFFFFF
        m.fp.seek(o)
        raw = m.fp.read(cs)
        num = (fs + m.sector_size - 1) // m.sector_size
        table = M._decrypt(raw, (key - 1) & 0xFFFFFFFF)
        offs = [int.from_bytes(table[i * 4:(i + 1) * 4], "little") for i in range(num + 1)]
        sec = M._decrypt(raw[offs[0]:offs[1]], key)

    print("sector len=%d type=0x%02X" % (len(sec), sec[0]))
    body = sec[1:]
    print("body head=%s" % body[:32].hex(" "))

    attempts = []
    for skip in range(0, 12):
        chunk = body[skip:]
        attempts.append(("zlib15 skip%d" % skip, lambda c=chunk: zlib.decompress(c)))
        attempts.append(("raw-def skip%d" % skip,
                         lambda c=chunk: zlib.decompress(c, -15)))
        attempts.append(("gzip skip%d" % skip,
                         lambda c=chunk: zlib.decompress(c, 47)))
        attempts.append(("bz2 skip%d" % skip, lambda c=chunk: bz2.decompress(c)))
        attempts.append(("lzma skip%d" % skip, lambda c=chunk: lzma.decompress(c)))

    hits = 0
    for label, fn in attempts:
        try:
            out = fn()
        except Exception:
            continue
        tag = " <== VER!" if out[:4] == b"VER " else ""
        print("  %-16s -> %6d bytes head=%r%s" % (label, len(out), out[:16], tag))
        hits += 1
    if not hits:
        print("  no standard decompressor accepted the data")


if __name__ == "__main__":
    main()

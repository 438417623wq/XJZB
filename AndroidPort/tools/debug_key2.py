"""Test all FIX_KEY variants, including the compressed-size form used by StormLib.

GetFileKey(name, dwFilePos, dwFileSize, dwFlags) is called with dwFileSize set
to the entry's *compressed* size in StormLib, so the key may be
    (base + blockpos) ^ csize
rather than ^ fsize.
"""

import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"

TARGETS = [
    ("StarDat.mpq", "arr\\flingy.dat"),
    ("StarDat.mpq", "arr\\techdata.dat"),
    ("StarDat.mpq", "arr\\units.dat"),
    ("StarDat.mpq", "tileset\\badlands.wpe"),
    ("StarDat.mpq", "tileset\\badlands.cv5"),
    ("StarDat.mpq", "scripts\\iscript.bin"),
    ("BrooDat.mpq", "tileset\\ice.vr4"),
    ("BrooDat.mpq", "(listfile)"),
]


def variants(name, rel, abs_off, cs, fs):
    base = M.hash_string(name, M.HASH_FILE_KEY)
    return {
        "base": base,
        "(base+rel)^fs": ((base + rel) ^ fs) & 0xFFFFFFFF,
        "(base+rel)^cs": ((base + rel) ^ cs) & 0xFFFFFFFF,
        "(base+abs)^fs": ((base + abs_off) ^ fs) & 0xFFFFFFFF,
        "(base+abs)^cs": ((base + abs_off) ^ cs) & 0xFFFFFFFF,
    }


def check_sector(data):
    """Return a short verdict for a decrypted sector/blob."""
    if not data:
        return "empty"
    ctype = data[0]
    if ctype == 0x02:
        try:
            out = zlib.decompress(data[1:])
            return "ZLIB OK out=%d" % len(out)
        except Exception as e:
            return "zlib hdr but fail (%s)" % e
    if ctype == 0x08:
        return "PKWARE implode"
    if ctype == 0x10:
        return "bzip2"
    return "ctype=0x%02X" % ctype


def main():
    for arc, name in TARGETS:
        path = os.path.join(ROOT, arc)
        with MPQ(path) as m:
            bi = m.find(name)
            if bi is None:
                print("%-14s %-26s NOT FOUND" % (arc, name))
                continue
            abs_off, cs, fs, flags, rel = m.block_table[bi]
            num = (fs + m.sector_size - 1) // m.sector_size
            multi = bool(flags & M.FLAG_COMPRESS) and not (flags & M.FLAG_SINGLE_UNIT) and fs > m.sector_size
            print("== %s :: %s  cs=%d fs=%d num=%d multi=%s"
                  % (arc, name, cs, fs, num, multi))

            m.fp.seek(abs_off)
            raw = m.fp.read(cs)

            for label, key in variants(name, rel, abs_off, cs, fs).items():
                if multi:
                    dec = M._decrypt(raw, (key - 1) & 0xFFFFFFFF)
                    got = False
                    for osize in (4, 2):
                        if (num + 1) * osize > len(dec):
                            continue
                        offs = [int.from_bytes(dec[i * osize:(i + 1) * osize], "little")
                                for i in range(num + 1)]
                        if (offs[0] >= (num + 1) * osize and offs[0] <= cs
                                and offs[-1] == cs
                                and all(offs[i] <= offs[i + 1] for i in range(num))):
                            sec = M._decrypt(raw[offs[0]:offs[1]], (key + 0) & 0xFFFFFFFF)
                            print("   %-15s TABLE OK osize=%d  s0: %s"
                                  % (label, osize, check_sector(sec)))
                            got = True
                            break
                    if not got:
                        print("   %-15s --" % label)
                else:
                    blob = M._decrypt(raw, key)
                    print("   %-15s %s" % (label, check_sector(blob)))
            print()


if __name__ == "__main__":
    main()

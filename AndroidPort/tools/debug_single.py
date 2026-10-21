"""Focused test: can we decompress a single-sector MPQ file?

flingy.dat (fsize=2760 < 4096) has no sector offset table, so it isolates the
encryption + compression path from the sector-table logic.
"""

import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def attempt(m, name):
    bi = m.find(name)
    if bi is None:
        print("%-26s NOT FOUND" % name)
        return
    abs_off, cs, fs, flags, rel = m.block_table[bi]
    print("%-26s abs=%d cs=%d fs=%d flags=0x%08X" % (name, abs_off, cs, fs, flags))

    m.fp.seek(abs_off)
    raw = m.fp.read(cs)
    print("   RAW head: %s" % raw[:24].hex(" "))

    base = M.hash_string(name, M.HASH_FILE_KEY)
    variants = {
        "no-key": None,
        "base": base,
        "fix(rel,fs)": ((base + rel) ^ fs) & 0xFFFFFFFF,
        "fix(abs,fs)": ((base + abs_off) ^ fs) & 0xFFFFFFFF,
    }
    for label, key in variants.items():
        if key is None:
            data = raw
        else:
            data = M._decrypt(raw, key)
        head = data[:24].hex(" ")
        ctype = data[0] if data else -1
        note = ""
        if ctype == 0x02:
            try:
                out = zlib.decompress(data[1:])
                note = " ZLIB OK out=%d" % len(out)
            except Exception as e:
                note = " zlib fail %s" % e
        print("   %-12s key=%-10s ctype=0x%02X  %s%s"
              % (label, ("--" if key is None else "%08X" % key), ctype, head[:23], note))


def main():
    path = os.path.join(ROOT, "StarDat.mpq")
    with MPQ(path) as m:
        for n in ("arr\\flingy.dat", "arr\\techdata.dat", "arr\\units.dat",
                  "tileset\\badlands.wpe"):
            attempt(m, n)
            print()


if __name__ == "__main__":
    main()

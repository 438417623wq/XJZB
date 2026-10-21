"""Diagnose MPQ block decryption: find the correct key formula + sector layout."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def try_offsets(table, num, csize, osize):
    if (num + 1) * osize > len(table):
        return None
    cand = [
        int.from_bytes(table[i * osize:(i + 1) * osize], "little")
        for i in range(num + 1)
    ]
    ok = (
        len(cand) == num + 1
        and cand[0] >= (num + 1) * osize
        and cand[0] <= csize
        and cand[-1] == csize
        and all(cand[i] <= cand[i + 1] for i in range(num))
    )
    return cand if ok else None


def try_file(m, name):
    bi = m.find(name)
    if bi is None:
        print("%-28s NOT FOUND" % name)
        return
    abs_off, cs, fs, flags, rel = m.block_table[bi]
    num = (fs + m.sector_size - 1) // m.sector_size
    multi = bool(flags & M.FLAG_COMPRESS) and not (flags & M.FLAG_SINGLE_UNIT) and fs > m.sector_size

    print("---- %s" % name)
    print("     abs=%d rel=%d csize=%d fsize=%d flags=0x%08X" % (abs_off, rel, cs, fs, flags))
    print("     header_offset=%d num_sectors=%d multi=%s" % (m.header_offset, num, multi))

    base = M.hash_string(name, M.HASH_FILE_KEY)
    cands = {
        "base": base,
        "fix(rel,fs)": ((base + rel) ^ fs) & 0xFFFFFFFF,
        "fix(abs,fs)": ((base + abs_off) ^ fs) & 0xFFFFFFFF,
        "fix(rel,cs)": ((base + rel) ^ cs) & 0xFFFFFFFF,
        "fix(abs,cs)": ((base + abs_off) ^ cs) & 0xFFFFFFFF,
    }

    m.fp.seek(abs_off)
    raw = m.fp.read(cs)

    for label, key in cands.items():
        dec = M._decrypt(raw, (key - 1) & 0xFFFFFFFF)
        for osize in (4, 2):
            offs = try_offsets(dec, num, cs, osize)
            if offs:
                print("     KEY MATCH %-12s key=0x%08X osize=%d first=%s last=%d"
                      % (label, key, osize, offs[:6], offs[-1]))
                # verify first sector decompresses
                s, e = offs[0], offs[1]
                sec = raw[s:e]
                sec = M._decrypt(sec, (key + 0) & 0xFFFFFFFF)
                print("        sector0 ctype=0x%02X len=%d" % (sec[0], len(sec)))
                return


def main():
    targets = [
        ("BrooDat.mpq", "(listfile)"),
        ("StarDat.mpq", "tileset\\badlands.cv5"),
        ("StarDat.mpq", "arr\\flingy.dat"),
        ("BrooDat.mpq", "tileset\\ice.vr4"),
    ]
    for arc, name in targets:
        path = os.path.join(ROOT, arc)
        with MPQ(path) as m:
            print("=== %s (header_offset=%d) ===" % (arc, m.header_offset))
            try:
                try_file(m, name)
            except Exception as e:
                print("   ERROR %r" % (e,))
            print()


if __name__ == "__main__":
    main()

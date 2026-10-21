"""Find ALL hash-table slots matching a filename.

StarCraft MPQs can hold several entries that share a name hash (locale
variants). find() returns the first; a dummy/stale variant would explain why
the key formula works for (listfile) but not for game assets.
"""

import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def find_all(m, name):
    h_a = M.hash_string(name, M.HASH_NAME_A)
    h_b = M.hash_string(name, M.HASH_NAME_B)
    h_o = M.hash_string(name, M.HASH_TABLE_OFFSET)
    start = h_o & (m.hash_table_size - 1)
    out = []
    for i in range(m.hash_table_size):
        idx = (start + i) & (m.hash_table_size - 1)
        a, b, locale, platform, bi = m.hash_table[idx]
        if bi == 0xFFFFFFFF:
            break
        if a == h_a and b == h_b:
            out.append((idx, locale, platform, bi))
    return out


def describe(m, name):
    slots = find_all(m, name)
    print("--- %s : %d matching slot(s)" % (name, len(slots)))
    for idx, locale, platform, bi in slots:
        if bi >= len(m.block_table):
            print("    slot%-6d locale=0x%04X plat=0x%04X block=%-6d OUT OF RANGE"
                  % (idx, locale, platform, bi))
            continue
        o, cs, fs, flags, rel = m.block_table[bi]
        print("    slot%-6d locale=0x%04X plat=0x%04X block=%-6d o=%-9d cs=%-8d fs=%-8d flags=0x%08X"
              % (idx, locale, platform, bi, o, cs, fs, flags))

        base = M.hash_string(name, M.HASH_FILE_KEY)
        m.fp.seek(o)
        raw = m.fp.read(min(cs, 1 << 20))
        for label, key in (("^fs", ((base + rel) ^ fs) & 0xFFFFFFFF),
                           ("^cs", ((base + rel) ^ cs) & 0xFFFFFFFF),
                           ("base", base)):
            dec = M._decrypt(raw, key)
            c = dec[0] if dec else -1
            note = ""
            if c == 0x02:
                try:
                    out = zlib.decompress(dec[1:])
                    note = " ZLIB OK out=%d" % len(out)
                except Exception as e:
                    note = " zlibfail(%s)" % str(e)[:30]
            if c in (0x01, 0x02, 0x08, 0x10, 0x20, 0x40, 0x80) or note:
                print("        key=%-6s 0x%08X ctype=0x%02X%s" % (label, key, c, note))


def main():
    targets = [
        ("BrooDat.mpq", "(listfile)"),
        ("BrooDat.mpq", "tileset\\ice.vr4"),
        ("StarDat.mpq", "arr\\flingy.dat"),
        ("StarDat.mpq", "tileset\\badlands.cv5"),
        ("StarDat.mpq", "unit\\marine.grp"),
    ]
    for arc, name in targets:
        path = os.path.join(ROOT, arc)
        with MPQ(path) as m:
            print("== %s" % arc)
            describe(m, name)
        print()


if __name__ == "__main__":
    main()

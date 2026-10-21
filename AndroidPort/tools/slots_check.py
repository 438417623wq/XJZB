"""Check for duplicate hash slots on failing entries, and compare with working ones."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive as S  # noqa: E402
from sc_archive import Archive  # noqa: E402

ROOT = r"F:\KF\XJZB"


def find_all(a, name):
    h_a = S.hash_string(name, S.HASH_NAME_A)
    h_b = S.hash_string(name, S.HASH_NAME_B)
    start = S.hash_string(name, S.HASH_TABLE_OFFSET) & (a.hash_table_size - 1)
    out = []
    for i in range(a.hash_table_size):
        idx = (start + i) & (a.hash_table_size - 1)
        x, y, loc, plat, bi = a.hash_table[idx]
        if bi == 0xFFFFFFFF:
            break
        if x == h_a and y == h_b:
            out.append((idx, loc, plat, bi))
    return out


def main():
    with Archive(os.path.join(ROOT, "BrooDat.mpq")) as a:
        for name in ("unit\\zerg\\zegShad.grp", "unit\\terran\\medic.grp",
                     "unit\\zerg\\Zlurker.grp"):
            slots = find_all(a, name)
            print("== %s  -> %d slot(s)" % (name, len(slots)))
            for idx, loc, plat, bi in slots:
                o, cs, fs, flags, rel = a.block_table[bi]
                print("    slot%-6d loc=0x%04X plat=0x%04X blk=%-5d o=%-9d cs=%-7d fs=%-7d flags=0x%08X"
                      % (idx, loc, plat, bi, o, cs, fs, flags))
            print()


if __name__ == "__main__":
    main()

"""Decisive scan: does ANY (name, block) pair decrypt to a valid stream?

The first decrypted byte depends only on the first 32-bit word, so the test is
O(1) per pair -- cheap enough to scan every candidate name against every block.

If the key formula is right we expect many hits; if only (listfile)@928 hits,
the formula or the name set is wrong.
"""

import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"

TILESETS = "badlands platform install ashworld jungle desert ice twilight".split()
PALETTES = """units tileset loading ofire bfire gfire terran zerg protoss wirefram
gamepal green blue red teal title font""".split()
SCRIPTS = "iscript images stat_txt orders upgrades weapons flingy sprites techdata".split()
UNITS = """
marine firebat medic ghost vulture goliath siege_tank scv wraith dropship
battlecruiser valkyrie zealot dragoon high_templar archon shuttle scout arbiter
carrier interceptor corsair dark_templar dark_archon reaver observer probe
zergling hydralisk lurker ultralisk defiler queen drone overlord mutalisk
guardian devourer scourge egg larva cocoon broodling
""".split()


def all_names():
    n = ["(listfile)", "(hash table)", "(block table)"]
    for t in TILESETS:
        for ext in ("cv5", "vx4", "vr4", "wpe", "dddata"):
            n.append("tileset\\%s.%s" % (t, ext))
    for p in PALETTES:
        n.append("palette\\%s.pal" % p)
    for s in SCRIPTS:
        n.append("scripts\\%s.bin" % s)
    for u in UNITS:
        n.append("unit\\%s.grp" % u)
        n.append("unit\\%s.grp" % u.replace("_", ""))
    for d in ("units", "flingy", "sprites", "images", "orders", "weapons",
              "upgrades", "techdata", "buttons", "sound"):
        n.append("arr\\%s.dat" % d)
    return sorted(set(n))


def first_byte(raw4, key):
    """Decrypt just the first byte of a block (one cipher step)."""
    seed1 = key & 0xFFFFFFFF
    seed2 = (0xEEEEEEEE + M._CRYPT[0x400 + (seed1 & 0xFF)]) & 0xFFFFFFFF
    word = int.from_bytes(raw4, "little")
    plain = (word ^ ((seed1 + seed2) & 0xFFFFFFFF)) & 0xFFFFFFFF
    return plain & 0xFF


def main():
    names = all_names()
    print("names=%d" % len(names))
    for arc in ("BrooDat.mpq", "StarDat.mpq"):
        path = os.path.join(ROOT, arc)
        with MPQ(path) as m:
            print("=" * 70)
            print("%s blocks=%d" % (arc, len(m.block_table)))
            m.fp.seek(0)
            data = m.fp.read()
            hits = []
            for name in names:
                base = M.hash_string(name, M.HASH_FILE_KEY)
                for bi, (o, cs, fs, flags, rel) in enumerate(m.block_table):
                    if not (flags & M.FLAG_ENCRYPTED):
                        continue
                    if cs < 4 or o + 4 > len(data):
                        continue
                    key = ((base + rel) ^ fs) & 0xFFFFFFFF if (flags & M.FLAG_FIX_KEY) else base
                    b0 = first_byte(data[o:o + 4], key)
                    if b0 in (0x02, 0x08):
                        hits.append((name, bi, fs, cs, b0))
            print("potential hits: %d" % len(hits))
            for name, bi, fs, cs, b0 in hits[:40]:
                o, cs2, fs2, flags, rel = m.block_table[bi]
                raw = data[o:o + cs2]
                key = ((M.hash_string(name, M.HASH_FILE_KEY) + rel) ^ fs2) & 0xFFFFFFFF
                dec = M._decrypt(raw, key)
                note = ""
                if dec[0] == 0x02:
                    try:
                        out = zlib.decompress(dec[1:])
                        note = "  *** ZLIB OK out=%d ***" % len(out)
                    except Exception as e:
                        note = "  zlibfail"
                print("   %-26s blk%-5d fs=%-8d cs=%-8d b0=0x%02X%s"
                      % (name, bi, fs, cs, b0, note))
            print()


if __name__ == "__main__":
    main()

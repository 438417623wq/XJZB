"""Hunt for the key that decrypts a StarCraft game file.

The block table is provably sane (sum of csize ~= filesize), so the target
block is real. We try many candidate keys to find which one yields a valid
compression-type byte.
"""

import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"

UNITS = """
marine firebat medic ghost vulture goliath siege_tank scv wraith dropship
battlecruiser valkyrie zealot dragoon high_templar archon shuttle scout arbiter
carrier interceptor corsair dark_templar dark_archon reaver observer probe
zergling hydralisk lurker ultralisk defiler queen drone overlord mutalisks
mutalisk guardian devourer scourge egg larva cocoon broodling
""".split()

NAMES = ["(listfile)", "(hash table)", "(block table)"]
for u in UNITS:
    NAMES.append("unit\\%s.grp" % u)
    NAMES.append("unit\\%s.grp" % u.replace("_", ""))
NAMES += [
    "arr\\flingy.dat", "arr\\units.dat", "arr\\sprites.dat", "arr\\images.dat",
    "arr\\weapons.dat", "arr\\orders.dat", "arr\\techdata.dat", "arr\\upgrades.dat",
    "scripts\\iscript.bin",
    "tileset\\badlands.cv5", "tileset\\badlands.vx4", "tileset\\badlands.vr4",
    "tileset\\badlands.wpe", "tileset\\jungle.vr4", "tileset\\ice.vr4",
]


def ctype(data):
    return data[0] if data else -1


def verdict(data):
    c = ctype(data)
    if c == 0x02:
        try:
            out = zlib.decompress(data[1:])
            return "ZLIB OK %d" % len(out)
        except Exception:
            return "0x02 but zlib failed"
    if c in (0x01, 0x08, 0x10, 0x20, 0x40, 0x80):
        return "candidate ctype=0x%02X" % c
    return None


def main():
    path = os.path.join(ROOT, "StarDat.mpq")
    with MPQ(path) as m:
        # --- 1. how do the flags look across the archive?
        combos = {}
        for (o, cs, fs, flags, rel) in m.block_table:
            combos[flags] = combos.get(flags, 0) + 1
        print("FLAG COMBOS in StarDat.mpq:")
        for f, n in sorted(combos.items(), key=lambda kv: -kv[1]):
            print("   0x%08X  x%d   (ENC=%s FIX=%s CMP=%s IMP=%s SU=%s)"
                  % (f, n, bool(f & M.FLAG_ENCRYPTED), bool(f & M.FLAG_FIX_KEY),
                     bool(f & M.FLAG_COMPRESS), bool(f & M.FLAG_IMPLODE),
                     bool(f & M.FLAG_SINGLE_UNIT)))
        print()

        # --- 2. a stored (unencrypted) entry would validate the pipeline
        stored = [(i, e) for i, e in enumerate(m.block_table)
                  if (e[3] & M.FLAG_EXISTS) and not (e[3] & M.FLAG_ENCRYPTED)]
        print("unencrypted entries: %d" % len(stored))
        for i, (o, cs, fs, flags, rel) in stored[:5]:
            m.fp.seek(o)
            raw = m.fp.read(min(cs, 32))
            print("   blk%-5d o=%-9d cs=%-7d fs=%-7d flags=0x%08X head=%s"
                  % (i, o, cs, fs, flags, raw[:16].hex(" ")))
        print()

        # --- 3. key hunt against the flingy.dat block
        bi = m.find("arr\\flingy.dat")
        abs_off, cs, fs, flags, rel = m.block_table[bi]
        print("target block %d: o=%d cs=%d fs=%d flags=0x%08X" % (bi, abs_off, cs, fs, flags))
        m.fp.seek(abs_off)
        raw = m.fp.read(cs)
        print("raw head: %s" % raw[:24].hex(" "))

        hits = 0
        for nm in NAMES:
            base = M.hash_string(nm, M.HASH_FILE_KEY)
            keys = {
                "base": base,
                "^fs": ((base + rel) ^ fs) & 0xFFFFFFFF,
                "^cs": ((base + rel) ^ cs) & 0xFFFFFFFF,
                "nofix": base,
            }
            for label, key in keys.items():
                v = verdict(M._decrypt(raw, key))
                if v:
                    print("   HIT %-22s %-6s key=0x%08X -> %s" % (nm, label, key, v))
                    hits += 1
        if not hits:
            print("   no candidate key produced a recognisable compression byte")


if __name__ == "__main__":
    main()

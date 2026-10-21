"""Test whether MPQ file keys use the BARE filename instead of the full path.

In the map archive, the key that validated the sector table came from
hash("scenario.chk"), not hash("staredit\\scenario.chk"). Apply the same idea
to the main game archives.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def sector_types(m, raw, key, cs, fs):
    """Decrypt the sector table + every sector; return ctypes or None."""
    num = (fs + m.sector_size - 1) // m.sector_size
    table = M._decrypt(raw, (key - 1) & 0xFFFFFFFF)
    if (num + 1) * 4 > len(table):
        return None
    offs = [int.from_bytes(table[i * 4:(i + 1) * 4], "little") for i in range(num + 1)]
    if not (offs[0] >= (num + 1) * 4 and offs[0] <= cs and offs[-1] == cs
            and all(offs[i] <= offs[i + 1] for i in range(num))):
        return None
    ctypes = []
    for i in range(num):
        sec = M._decrypt(raw[offs[i]:offs[i + 1]], (key + i) & 0xFFFFFFFF)
        ctypes.append(sec[0] if sec else -1)
    return ctypes


def evaluate(m, name, raw, cs, fs, flags, rel, label):
    base = M.hash_string(name, M.HASH_FILE_KEY)
    keys = [("base", base)]
    if flags & M.FLAG_FIX_KEY:
        keys.append(("^fs", ((base + rel) ^ fs) & 0xFFFFFFFF))
        keys.append(("^cs", ((base + rel) ^ cs) & 0xFFFFFFFF))

    best = None
    for kl, key in keys:
        if fs <= m.sector_size:
            sec = M._decrypt(raw, key)
            c = sec[0] if sec else -1
            valid = c in (0x02, 0x08, 0x01, 0x10)
            if valid:
                print("    %-22s %-5s key=0x%08X  single-sector ctype=0x%02X  <== VALID"
                      % (label, kl, key, c))
                best = c
        else:
            ct = sector_types(m, raw, key, cs, fs)
            if ct:
                kinds = {}
                for c in ct:
                    kinds[c] = kinds.get(c, 0) + 1
                good = sum(v for k, v in kinds.items() if k in (0x02, 0x08, 0x01, 0x10))
                print("    %-22s %-5s key=0x%08X  sectors=%d valid=%d %s"
                      % (label, kl, key, len(ct), good, dict(sorted(kinds.items()))))
                if good == len(ct):
                    best = ct
    return best


def main():
    # --- map first: we know scenario.chk works
    print("### MAP check (control)")
    mp = os.path.join(ROOT, "maps", "(2)Bottleneck.scm")
    with MPQ(mp) as m:
        o, cs, fs, flags, rel = m.block_table[0]
        m.fp.seek(o)
        raw = m.fp.read(cs)
        print("  blk0 cs=%d fs=%d flags=0x%08X" % (cs, fs, flags))
        for nm in ("scenario.chk", "staredit\\scenario.chk"):
            evaluate(m, nm, raw, cs, fs, flags, rel, nm)

    # --- now the game archives, bare vs full path
    print("\n### StarDat / BrooDat: bare filename vs full path")
    targets = [
        ("StarDat.mpq", "arr\\flingy.dat"),
        ("StarDat.mpq", "tileset\\badlands.wpe"),
        ("StarDat.mpq", "tileset\\badlands.cv5"),
        ("StarDat.mpq", "scripts\\iscript.bin"),
        ("BrooDat.mpq", "tileset\\ice.vr4"),
    ]
    for arc, full in targets:
        with MPQ(os.path.join(ROOT, arc)) as m:
            bi = m.find(full)
            if bi is None:
                print("  %s :: %s NOT FOUND" % (arc, full))
                continue
            o, cs, fs, flags, rel = m.block_table[bi]
            m.fp.seek(o)
            raw = m.fp.read(cs)
            print("  %s :: %s  blk=%d cs=%d fs=%d flags=0x%08X"
                  % (arc, full, bi, cs, fs, flags))
            bare = full.split("\\")[-1]
            for nm in {full, bare}:
                evaluate(m, nm, raw, cs, fs, flags, rel, nm)
            print()


if __name__ == "__main__":
    main()

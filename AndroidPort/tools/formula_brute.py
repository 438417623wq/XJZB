"""Brute-force many key-formula variants against a single-sector file.

flingy.dat (fs=2760 < 4096) has no sector table, so a correct key must make
the first decrypted byte a valid compression type and decompress cleanly.
"""

import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def name_variants(name):
    parts = name.split("\\")
    base = parts[-1]
    stem = base.rsplit(".", 1)[0]
    ext = base.rsplit(".", 1)[-1]
    v = {
        "orig": name,
        "upper": name.upper(),
        "lower": name.lower(),
        "nodir": base,
        "stem": stem,
        "fwd": name.replace("\\", "/"),
        "doubleslash": name.replace("\\", "\\\\"),
    }
    return v


def formulas(base, rel, cs, fs):
    M32 = 0xFFFFFFFF
    out = {
        "base": base,
        "(b+rel)^fs": ((base + rel) ^ fs) & M32,
        "(b+rel)^cs": ((base + rel) ^ cs) & M32,
        "b^(rel+fs)": (base ^ ((rel + fs) & M32)) & M32,
        "b+(rel^fs)": (base + (rel ^ fs)) & M32,
        "(b^rel)+fs": ((base ^ rel) + fs) & M32,
        "(b^fs)+rel": ((base ^ fs) + rel) & M32,
        "b^rel^fs": (base ^ rel ^ fs) & M32,
        "b+rel-fs": (base + rel - fs) & M32,
        "b-rel+fs": (base - rel + fs) & M32,
        "(b+fs)^rel": ((base + fs) ^ rel) & M32,
        "(b+cs)^rel": ((base + cs) ^ rel) & M32,
        "b+cs": (base + cs) & M32,
        "b^cs": (base ^ cs) & M32,
    }
    return out


def check(raw, key, fs):
    try:
        dec = M._decrypt(raw, key)
    except Exception:
        return None
    if not dec:
        return None
    c = dec[0]
    if c == 0x02:
        try:
            out = zlib.decompress(dec[1:])
            if len(out) == fs:
                return ("zlib exact", out)
            return ("zlib", out)
        except Exception:
            return None
    if c == 0x08:
        return ("implode", None)
    return None


def main():
    path = os.path.join(ROOT, "StarDat.mpq")
    with MPQ(path) as m:
        for target in ("arr\\flingy.dat", "arr\\techdata.dat", "tileset\\badlands.wpe"):
            bi = m.find(target)
            o, cs, fs, flags, rel = m.block_table[bi]
            m.fp.seek(o)
            raw = m.fp.read(cs)
            print("== %s blk=%d o=%d cs=%d fs=%d flags=0x%08X" % (target, bi, o, cs, fs, flags))
            hits = 0
            for nlabel, nm in name_variants(target).items():
                base = M.hash_string(nm, M.HASH_FILE_KEY)
                for flabel, key in formulas(base, rel, cs, fs).items():
                    r = check(raw, key, fs)
                    if r:
                        print("   HIT name=%-12s formula=%-12s key=0x%08X -> %s"
                              % (nlabel, flabel, key, r[0]))
                        hits += 1
            print("   hits: %d" % hits)
            print()


if __name__ == "__main__":
    main()

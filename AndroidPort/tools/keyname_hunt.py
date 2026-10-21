"""Brute-force the key-name form for a specific failing GRP entry.

Decryption is correct only when the implode stream's first byte is 0 or 1
(the literal-mode flag). Use that as the acceptance test.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sc_archive import Archive, decrypt, hash_string, FLAG_ENCRYPTED, FLAG_FIX_KEY, FLAG_COMPRESS  # noqa: E402

ROOT = r"F:\KF\XJZB"


def variants(name):
    parts = name.split("\\")
    bare = parts[-1]
    stem = bare.rsplit(".", 1)[0]
    out = {
        "bare": bare,
        "full": name,
        "stem": stem,
        "bare_noext_upper": stem.upper(),
        "dir_stem": "\\".join(parts[:-1] + [stem]),
        "bare_swapcase": bare.swapcase(),
    }
    # common StarCraft internal aliases
    out["bare_l"] = bare.lower()
    return out


def first_byte_ok(data):
    return len(data) > 1 and data[0] in (0, 1)


def main():
    targets = [
        "unit\\zerg\\zegShad.grp",
        "unit\\zerg\\zucShad.grp",
        "unit\\protoss\\pneGlow.grp",
        "unit\\protoss\\pbaGlow.grp",
    ]
    with Archive(os.path.join(ROOT, "BrooDat.mpq")) as a:
        for name in targets:
            bi = a.find(name)
            if bi is None:
                print("%s NOT FOUND" % name)
                continue
            o, cs, fs, flags, rel = a.block_table[bi]
            a.fp.seek(o)
            raw = a.fp.read(cs)
            print("== %s  blk=%d cs=%d fs=%d flags=0x%08X rel=%d"
                  % (name, bi, cs, fs, flags, rel))
            got = False
            for label, kn in variants(name).items():
                base = hash_string(kn, 3)
                keys = {"base": base}
                if flags & FLAG_FIX_KEY:
                    keys["^fs"] = ((base + rel) ^ fs) & 0xFFFFFFFF
                    keys["^cs"] = ((base + rel) ^ cs) & 0xFFFFFFFF
                for kl, key in keys.items():
                    if fs <= a.sector_size:
                        body = decrypt(raw, key)
                        if first_byte_ok(body):
                            print("   HIT %-16s %-5s key=0x%08X first=%d"
                                  % (label, kl, key, body[0]))
                            got = True
                        elif body and body[0] in (0x02, 0x08):
                            print("   hit? %-15s %-5s first=0x%02X" % (label, kl, body[0]))
            if not got:
                print("   no key-name variant produced a valid stream header")
            print()


if __name__ == "__main__":
    main()

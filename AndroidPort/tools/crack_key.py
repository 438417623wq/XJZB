"""Recover the real MPQ file key from known plaintext.

An MPQ sector that uses zlib begins with bytes: 02 78 (9C|01|DA|5E) ..
so three of the first four plaintext bytes are known. Combined with the cipher

    plain_word0 = cipher_word0 ^ (key + seed2_1)
    seed2_1     = 0xEEEEEEEE + crypt[0x400 + (key & 0xFF)]

we can enumerate 256 low bytes x 4 zlib flags x 256 unknown 4th bytes and
solve for the key, keeping only self-consistent candidates.
"""

import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"
ZLIB_FLG = (0x9C, 0x01, 0xDA, 0x5E)


def candidate_keys(cipher_word0):
    out = []
    for k0 in range(256):
        s2 = (0xEEEEEEEE + M._CRYPT[0x400 + k0]) & 0xFFFFFFFF
        for flg in ZLIB_FLG:
            for b3 in range(256):
                plain = 0x02 | (0x78 << 8) | (flg << 16) | (b3 << 24)
                key = ((cipher_word0 ^ plain) - s2) & 0xFFFFFFFF
                if (key & 0xFF) == k0:
                    out.append(key)
    return out


def verify(raw, key, fs, cs, sector_size):
    try:
        num = (fs + sector_size - 1) // sector_size
        if fs <= sector_size:
            blob = M._decrypt(raw, key)
            if not blob or blob[0] != 0x02:
                return None
            return zlib.decompress(blob[1:])
        table = M._decrypt(raw, (key - 1) & 0xFFFFFFFF)
        offs = [int.from_bytes(table[i * 4:(i + 1) * 4], "little") for i in range(num + 1)]
        if offs[0] < (num + 1) * 4 or offs[0] > cs or offs[-1] != cs:
            return None
        if any(offs[i] > offs[i + 1] for i in range(num)):
            return None
        sec = M._decrypt(raw[offs[0]:offs[1]], key)
        if not sec or sec[0] != 0x02:
            return None
        return zlib.decompress(sec[1:])
    except Exception:
        return None


def crack(arc, name):
    path = os.path.join(ROOT, arc)
    with MPQ(path) as m:
        bi = m.find(name)
        if bi is None:
            print("%s :: %s NOT FOUND" % (arc, name))
            return
        o, cs, fs, flags, rel = m.block_table[bi]
        print("== %s :: %s  blk=%d o=%d cs=%d fs=%d flags=0x%08X rel=%d"
              % (arc, name, bi, o, cs, fs, flags, rel))
        m.fp.seek(o)
        raw = m.fp.read(cs)
        cipher_word0 = int.from_bytes(raw[:4], "little")

        base = M.hash_string(name, M.HASH_FILE_KEY)
        print("   hash(name,FILE_KEY)=0x%08X" % base)
        print("   formulas: (base+rel)^fs=0x%08X  (base+rel)^cs=0x%08X  base=0x%08X"
              % (((base + rel) ^ fs) & 0xFFFFFFFF,
                 ((base + rel) ^ cs) & 0xFFFFFFFF, base))

        cands = candidate_keys(cipher_word0)
        print("   candidate keys: %d" % len(cands))
        found = False
        for key in cands:
            out = verify(raw, key, fs, cs, m.sector_size)
            if out is not None:
                print("   *** CRACKED key=0x%08X  decompressed=%d bytes" % (key, len(out)))
                print("       out head: %r" % out[:48])
                # how does it relate to base?
                print("       base=0x%08X  key-base=0x%08X  key^base=0x%08X"
                      % (base, (key - base) & 0xFFFFFFFF, key ^ base))
                found = True
                break
        if not found:
            print("   no key recovered (file may not be zlib-compressed)")


def main():
    crack("StarDat.mpq", "arr\\flingy.dat")
    print()
    crack("StarDat.mpq", "tileset\\badlands.wpe")


if __name__ == "__main__":
    main()

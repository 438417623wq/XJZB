"""Final systematic attempt at the PKWARE implode header layout.

Oracle: the first emitted symbol must be the literal 'V' (0x56), since
scenario.chk starts with 'VER ' and no match is possible with empty history.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
import pkware  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


class BR:
    def __init__(self, data, bitpos=0):
        self.d = data
        self.p = bitpos // 8
        self.b = 0
        self.c = 0
        if bitpos % 8:
            self.b = data[self.p] >> (bitpos % 8)
            self.c = 8 - (bitpos % 8)
            self.p += 1

    def bits(self, n):
        while self.c < n:
            if self.p < len(self.d):
                self.b |= self.d[self.p] << self.c
                self.p += 1
            self.c += 8
        v = self.b & ((1 << n) - 1)
        self.b >>= n
        self.c -= n
        return v


def complete(lengths, n):
    try:
        h = pkware.Huffman(lengths, n)
    except Exception:
        return None
    left = 1
    for ln in range(1, pkware.MAXBITS + 1):
        left <<= 1
        left -= h.count[ln]
    return h if left == 0 else None


def v_flags_first(body, width):
    br = BR(body)
    flags = [br.bits(1) for _ in range(256)]
    litlen = [0] * 256
    for i in range(256):
        if flags[i]:
            litlen[i] = br.bits(width)
    return litlen, br


def v_interleaved(body, width):
    br = BR(body)
    litlen = [0] * 256
    for i in range(256):
        if br.bits(1):
            litlen[i] = br.bits(width)
    return litlen, br


def v_lenfirst_then_lit(body, width):
    br = BR(body)
    lenlen = [0] * 16
    for i in range(16):
        if br.bits(1):
            lenlen[i] = br.bits(width)
    litlen = [0] * 256
    for i in range(256):
        if br.bits(1):
            litlen[i] = br.bits(width)
    return litlen, br


VARIANTS = {
    "interleaved8": lambda b: v_interleaved(b, 8),
    "interleaved4": lambda b: v_interleaved(b, 4),
    "flagsfirst8": lambda b: v_flags_first(b, 8),
    "flagsfirst5": lambda b: v_flags_first(b, 5),
    "lenfirst8": lambda b: v_lenfirst_then_lit(b, 8),
}


def main():
    mp = os.path.join(ROOT, "maps", "(2)Bottleneck.scm")
    with MPQ(mp) as m:
        o, cs, fs, flags, rel = m.block_table[0]
        key = M.hash_string("scenario.chk", M.HASH_FILE_KEY)
        if flags & M.FLAG_FIX_KEY:
            key = ((key + rel) ^ fs) & 0xFFFFFFFF
        m.fp.seek(o)
        raw = m.fp.read(cs)
        num = (fs + m.sector_size - 1) // m.sector_size
        table = M._decrypt(raw, (key - 1) & 0xFFFFFFFF)
        offs = [int.from_bytes(table[i * 4:(i + 1) * 4], "little") for i in range(num + 1)]
        sec = M._decrypt(raw[offs[0]:offs[1]], key)

    for skip in range(0, 5):
        body = sec[1 + skip:]
        for vname, fn in VARIANTS.items():
            try:
                litlen, br = fn(body)
            except Exception:
                continue
            if any(l > 16 for l in litlen):
                continue
            h = complete(litlen, 256)
            if not h:
                continue
            nzc = sum(1 for l in litlen if l)
            # try decoding first symbol with a flag bit, and without
            for needflag in (True, False):
                try:
                    br2 = BR(body)
                    # replay header to position br2 identically
                    litlen2, br2 = fn(body)
                    if needflag:
                        if br2.bits(1) != 0:
                            continue
                    sym = h.decode(br2)
                except Exception:
                    continue
                if sym == 0x56:
                    print("*** SOLVED skip=%d variant=%s needflag=%s nzc=%d"
                          % (skip, vname, needflag, nzc))
                    return
                print("    skip=%d %-13s needflag=%-5s nzc=%-4d first=0x%02X"
                      % (skip, vname, needflag, nzc, sym))
    print("\nno variant produced 'V'")


if __name__ == "__main__":
    main()

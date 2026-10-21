"""Brute-force the PKWARE implode header layout using a known plaintext oracle.

scenario.chk output must begin with the bytes 'V','E','R',' ' (56 45 52 20),
and the first symbol emitted cannot be a match (no history yet), so it must be
the literal 0x56. We try many header interpretations until one decodes to 'V'.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
import pkware  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


class BR:
    def __init__(self, data):
        self.d = data
        self.p = 0
        self.b = 0
        self.c = 0

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


def build(lengths, n):
    """Return (Huffman, left) using canonical construction; None if malformed."""
    try:
        h = pkware.Huffman(lengths, n)
    except Exception:
        return None
    left = 1
    for ln in range(1, pkware.MAXBITS + 1):
        left <<= 1
        left -= h.count[ln]
    return (h, left)


def parse_and_decode(body, start, lenwidth, maxlen):
    br = BR(body[start:])
    litlen = [0] * 256
    for i in range(256):
        if br.bits(1):
            litlen[i] = br.bits(lenwidth)
    if any(l > maxlen for l in litlen):
        return None
    lt = build(litlen, 256)
    if not lt:
        return None
    lit, left = lt
    if left != 0:
        return None  # require a complete code

    # first symbol: 1 flag bit then a literal (must be a literal: no history)
    flag = br.bits(1)
    if flag != 0:
        return None
    sym = lit.decode(br)
    return sym


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
        body = sec[1:]
        print("body len=%d head=%s" % (len(body), body[:24].hex(" ")))

    found = []
    for start in range(0, 17):
        for lenwidth in (8, 4, 5, 6):
            for maxlen in (15, 16):
                try:
                    sym = parse_and_decode(body, start, lenwidth, maxlen)
                except Exception:
                    continue
                if sym == 0x56:
                    print("*** MATCH start=%d lenwidth=%d maxlen=%d -> literal 'V'"
                          % (start, lenwidth, maxlen))
                    found.append((start, lenwidth, maxlen))
                elif sym is not None:
                    print("    start=%-3d lenwidth=%d maxlen=%-3d first literal=0x%02X %r"
                          % (start, lenwidth, maxlen, sym, chr(sym) if 32 <= sym < 127 else "."))
    if not found:
        print("\nno interpretation produced 'V' as the first literal")


if __name__ == "__main__":
    main()

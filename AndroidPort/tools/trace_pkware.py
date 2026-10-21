"""Trace the first bits of a PKWARE implode sector to find the real format."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


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
        print("sector0 length=%d ctype=0x%02X" % (len(sec), sec[0]))
        print("bytes: %s" % sec[:48].hex(" "))

        body = sec[1:]
        # LSB-first bit reader
        pos = 0
        buf = 0
        cnt = 0

        def bits(n):
            nonlocal pos, buf, cnt
            while cnt < n:
                if pos < len(body):
                    buf |= body[pos] << cnt
                    pos += 1
                cnt += 8
            v = buf & ((1 << n) - 1)
            buf >>= n
            cnt -= n
            return v

        print("\nfirst 40 literal-length entries (flag, value):")
        nz = 0
        for i in range(40):
            f = bits(1)
            if f:
                v = bits(8)
                nz += 1
                print("   lit[%3d] flag=1 len=%d" % (i, v))
            else:
                print("   lit[%3d] flag=0" % i)

        # also show as a plain bit string for inspection
        print("\nraw first 12 bytes of body: %s" % body[:12].hex(" "))
        bits_msb = "".join(format(b, "08b") for b in body[:6])
        print("MSB-first bit string        : %s" % bits_msb)
        bits_lsb = "".join(format(b, "08b")[::-1] for b in body[:6])
        print("LSB-first bit string        : %s" % bits_lsb)


if __name__ == "__main__":
    main()

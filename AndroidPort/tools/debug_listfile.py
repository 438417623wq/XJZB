"""Debug the (listfile) extraction from BrooDat.mpq."""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def main():
    path = os.path.join(ROOT, "BrooDat.mpq")
    with MPQ(path) as m:
        for name in ("(listfile)", "(LISTFILE)", "listfile"):
            bi = m.find(name)
            print("%-14s block_index=%s" % (name, bi))
            if bi is None:
                continue
            off, cs, fs, flags, rel = m.block_table[bi]
            print("   offset=%d csize=%d size=%d flags=0x%08X" % (off, cs, fs, flags))
            print("   ENCRYPTED=%s COMPRESS=%s SINGLE_UNIT=%s FIX_KEY=%s SECTOR_CRC=%s"
                  % (bool(flags & M.FLAG_ENCRYPTED), bool(flags & M.FLAG_COMPRESS),
                     bool(flags & M.FLAG_SINGLE_UNIT), bool(flags & M.FLAG_FIX_KEY),
                     bool(flags & M.FLAG_SECTOR_CRC)))
            m.fp.seek(off)
            raw = m.fp.read(min(cs, 96))
            print("   raw head: %s" % raw[:48].hex(" "))
            try:
                data = m.read(name)
                print("   read OK len=%d" % len(data))
                print("   head: %s" % data[:64].hex(" "))
                print("   text: %r" % data[:120])
            except Exception as e:
                print("   read FAILED: %r" % (e,))

                # Manual attempt: treat as multi-sector with encryption
                key = M.hash_string(name, M.HASH_FILE_KEY)
                if flags & M.FLAG_FIX_KEY:
                    key = ((key + off) ^ fs) & 0xFFFFFFFF
                m.fp.seek(off)
                rawfull = m.fp.read(cs)
                dec = M._decrypt(rawfull, (key - 1) & 0xFFFFFFFF)
                num = (fs + m.sector_size - 1) // m.sector_size
                print("   num sectors=%d sector_size=%d" % (num, m.sector_size))
                print("   decrypted table head: %s" % dec[:64].hex(" "))
                osize = 4
                offsets = [int.from_bytes(dec[i * osize:(i + 1) * osize], "little")
                           for i in range(min(num + 1, 12))]
                print("   offsets(first12)=%s" % offsets)


if __name__ == "__main__":
    main()

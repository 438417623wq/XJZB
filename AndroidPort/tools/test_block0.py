"""Decisive test: decrypt block 0 of each archive using the (listfile) key.

StarDat block 0 and BrooDat block 0 have identical (offset=32, csize=74779,
size=199888, flags=0x80030200). If BrooDat's decrypts, StarDat's must too --
the key depends only on (name, rel_offset, size), which are identical.
"""

import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def probe_block0(arc):
    path = os.path.join(ROOT, arc)
    with MPQ(path) as m:
        o, cs, fs, flags, rel = m.block_table[0]
        print("== %s  blk0: o=%d cs=%d fs=%d flags=0x%08X rel=%d" % (arc, o, cs, fs, flags, rel))

        # also report where find() thinks (listfile) lives
        bi = m.find("(listfile)")
        print("   find('(listfile)') -> %s" % bi)

        m.fp.seek(o)
        raw = m.fp.read(cs)

        base = M.hash_string("(listfile)", M.HASH_FILE_KEY)
        for label, key in (
            ("(base+rel)^fs", ((base + rel) ^ fs) & 0xFFFFFFFF),
            ("(base+rel)^cs", ((base + rel) ^ cs) & 0xFFFFFFFF),
            ("base", base),
        ):
            num = (fs + m.sector_size - 1) // m.sector_size
            table = M._decrypt(raw, (key - 1) & 0xFFFFFFFF)
            offs = [int.from_bytes(table[i * 4:(i + 1) * 4], "little") for i in range(num + 1)]
            ok = (offs[0] >= (num + 1) * 4 and offs[0] <= cs and offs[-1] == cs
                  and all(offs[i] <= offs[i + 1] for i in range(num)))
            note = ""
            if ok:
                sec = M._decrypt(raw[offs[0]:offs[1]], (key + 0) & 0xFFFFFFFF)
                note = "s0 ctype=0x%02X" % sec[0]
                if sec[0] == 0x02:
                    try:
                        out = zlib.decompress(sec[1:])
                        note += " ZLIB out=%d | %r" % (len(out), out[:40])
                    except Exception as e:
                        note += " zlibfail %s" % e
            print("   key=%-14s 0x%08X  tableOK=%-5s %s" % (label, key, ok, note))
        print()


def main():
    for arc in ("BrooDat.mpq", "StarDat.mpq"):
        try:
            probe_block0(arc)
        except Exception as e:
            print("   ERROR %r" % (e,))


if __name__ == "__main__":
    main()

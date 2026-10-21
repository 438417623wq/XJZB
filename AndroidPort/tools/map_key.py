"""Try to decrypt scenario.chk inside a map archive -- a controlled cipher test.

We know the map archives contain plaintext nearby (the name list), so if the
cipher is correct the scenario key must reveal a 'VER ' CHK chunk.
"""

import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def attempt(raw, key, fs, cs, sector_size, label):
    num = (fs + sector_size - 1) // sector_size
    if fs <= sector_size:
        blob = M._decrypt(raw, key)
        c = blob[0] if blob else -1
        note = "single ctype=0x%02X" % c
        if c == 0x02:
            try:
                out = zlib.decompress(blob[1:])
                note += " zlib=%d head=%r" % (len(out), out[:8])
            except Exception as e:
                note += " zlibfail"
        print("   %-18s key=0x%08X %s" % (label, key, note))
        return

    table = M._decrypt(raw, (key - 1) & 0xFFFFFFFF)
    offs = [int.from_bytes(table[i * 4:(i + 1) * 4], "little") for i in range(num + 1)]
    ok = (offs[0] >= (num + 1) * 4 and offs[0] <= cs and offs[-1] == cs
          and all(offs[i] <= offs[i + 1] for i in range(num)))
    if not ok:
        print("   %-18s key=0x%08X table invalid" % (label, key))
        return
    sec = M._decrypt(raw[offs[0]:offs[1]], key)
    c = sec[0] if sec else -1
    note = "table OK ctype=0x%02X" % c
    if c == 0x02:
        try:
            out = zlib.decompress(sec[1:])
            note += " zlib=%d head=%r" % (len(out), out[:8])
            if out[:4] == b"VER ":
                note += "  *** CHK FOUND ***"
        except Exception:
            note += " zlibfail"
    print("   %-18s key=0x%08X %s" % (label, key, note))


def main():
    path = os.path.join(ROOT, "maps", "(2)Bottleneck.scm")
    with MPQ(path) as m:
        o, cs, fs, flags, rel = m.block_table[0]
        print("blk0 o=%d cs=%d fs=%d flags=0x%08X rel=%d sector=%d"
              % (o, cs, fs, flags, rel, m.sector_size))
        m.fp.seek(o)
        raw = m.fp.read(cs)

        for nm in ("staredit\\scenario.chk", "scenario.chk", "staredit/scenario.chk",
                   "(listfile)", "blizzard_2.cnd"):
            base = M.hash_string(nm, M.HASH_FILE_KEY)
            print(" name=%s base=0x%08X" % (nm, base))
            attempt(raw, base, fs, cs, m.sector_size, "base")
            attempt(raw, ((base + rel) ^ fs) & 0xFFFFFFFF, fs, cs, m.sector_size, "(b+rel)^fs")
            attempt(raw, ((base + rel) ^ cs) & 0xFFFFFFFF, fs, cs, m.sector_size, "(b+rel)^cs")
            print()


if __name__ == "__main__":
    main()

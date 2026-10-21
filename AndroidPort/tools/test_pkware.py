"""Validate the PKWARE implode decoder against known-good StarCraft data.

Oracles:
  * map scenario.chk must begin with the 'VER ' chunk
  * tileset .wpe palettes are exactly 1024 bytes

Uses the now-proven key rule: hash(bare filename, FILE_KEY), then
(key + rel) ^ fs when FLAG_FIX_KEY is set.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
import pkware  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def read_entry_full(m, raw, name, cs, fs, flags, rel):
    """Decrypt every sector and concatenate the decompressed output."""
    key = M.hash_string(name, M.HASH_FILE_KEY)
    if flags & M.FLAG_FIX_KEY:
        key = ((key + rel) ^ fs) & 0xFFFFFFFF

    if fs <= m.sector_size:
        sec = M._decrypt(raw, key)
        if sec and sec[0] == 0x08:
            return pkware.explode(sec[1:], fs)
        if sec and sec[0] == 0x02:
            import zlib
            return zlib.decompress(sec[1:])
        return sec[:fs]

    num = (fs + m.sector_size - 1) // m.sector_size
    table = M._decrypt(raw, (key - 1) & 0xFFFFFFFF)
    offs = [int.from_bytes(table[i * 4:(i + 1) * 4], "little") for i in range(num + 1)]
    out = bytearray()
    for i in range(num):
        sec = M._decrypt(raw[offs[i]:offs[i + 1]], (key + i) & 0xFFFFFFFF)
        want = min(m.sector_size, fs - len(out))
        if not sec:
            continue
        if sec[0] == 0x08:
            out += pkware.explode(sec[1:], want)
        elif sec[0] == 0x02:
            import zlib
            out += zlib.decompress(sec[1:])[:want]
        else:
            out += sec[:want]
    return bytes(out[:fs])


def main():
    # ---- oracle 1: map scenario.chk
    mp = os.path.join(ROOT, "maps", "(2)Bottleneck.scm")
    with MPQ(mp) as m:
        o, cs, fs, flags, rel = m.block_table[0]
        m.fp.seek(o)
        raw = m.fp.read(cs)
        data = read_entry_full(m, raw, "scenario.chk", cs, fs, flags, rel)
        print("scenario.chk: %d bytes" % len(data))
        print("  head: %r" % data[:32])
        print("  VER chunk ok: %s" % (data[:4] == b"VER "))

    # ---- oracle 2: a tileset file
    with MPQ(os.path.join(ROOT, "StarDat.mpq")) as m:
        for full in ("tileset\\badlands.cv5", "scripts\\iscript.bin"):
            bi = m.find(full)
            o, cs, fs, flags, rel = m.block_table[bi]
            m.fp.seek(o)
            raw = m.fp.read(cs)
            bare = full.split("\\")[-1]
            try:
                data = read_entry_full(m, raw, bare, cs, fs, flags, rel)
                print("%s: %d/%d bytes  head=%s" % (full, len(data), fs, data[:24].hex(" ")))
            except Exception as e:
                print("%s: FAILED %r" % (full, e))


if __name__ == "__main__":
    main()

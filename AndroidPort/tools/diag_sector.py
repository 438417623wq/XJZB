"""Decode the first scenario.chk sector with no target size and inspect output."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
import pkware  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def get_sector(arc_path, name, blk=0, sector_index=0):
    with MPQ(arc_path) as m:
        o, cs, fs, flags, rel = m.block_table[blk]
        key = M.hash_string(name, M.HASH_FILE_KEY)
        if flags & M.FLAG_FIX_KEY:
            key = ((key + rel) ^ fs) & 0xFFFFFFFF
        m.fp.seek(o)
        raw = m.fp.read(cs)
        num = (fs + m.sector_size - 1) // m.sector_size
        table = M._decrypt(raw, (key - 1) & 0xFFFFFFFF)
        offs = [int.from_bytes(table[i * 4:(i + 1) * 4], "little") for i in range(num + 1)]
        sec = M._decrypt(raw[offs[sector_index]:offs[sector_index + 1]],
                         (key + sector_index) & 0xFFFFFFFF)
        return sec, fs, num, offs


def main():
    mp = os.path.join(ROOT, "maps", "(2)Bottleneck.scm")
    sec, fs, num, offs = get_sector(mp, "scenario.chk")
    print("sector0: len=%d type=0x%02X  total sectors=%d  fs=%d" % (len(sec), sec[0], num, fs))
    print("sector sizes:", [offs[i + 1] - offs[i] for i in range(min(6, num))])

    body = sec[1:]
    out = None
    try:
        out = pkware.explode(body)
        print("decoded %d bytes (no limit)" % len(out))
    except EOFError as e:
        print("EOFError: %s" % e)
    except Exception as e:
        print("%r" % (e,))
    if out is None:
        # decode incrementally to capture partial output
        br = pkware.Bits(body)
        lit = br.bits(8)
        dic = br.bits(8)
        print("lit=%d dic=%d" % (lit, dic))
        buf = bytearray()
        try:
            while len(buf) < 20000:
                if br.bits(1):
                    symbol = pkware.decode(br, pkware._LENCODE)
                    length = pkware.BASE[symbol] + br.bits(pkware.EXTRA[symbol])
                    if length == pkware.END_CODE:
                        print("END CODE at %d bytes" % len(buf))
                        break
                    s2 = 2 if length == 2 else dic
                    dist = (pkware.decode(br, pkware._DISTCODE) << s2) + br.bits(s2) + 1
                    if dist > len(buf):
                        print("BAD DIST %d > %d at offset %d" % (dist, len(buf), len(buf)))
                        break
                    src = len(buf) - dist
                    for i in range(length):
                        buf.append(buf[src + i])
                else:
                    buf.append(pkware.decode(br, pkware._LITCODE) if lit else br.bits(8))
        except EOFError:
            print("EOF at %d bytes" % len(buf))
        except Exception as e:
            print("%r at %d bytes" % (e, len(buf)))
        print("partial head: %r" % bytes(buf[:64]))
        print("VER ok:", buf[:4] == b"VER ")


if __name__ == "__main__":
    main()

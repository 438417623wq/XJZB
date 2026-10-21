"""Scan every readable (stored) entry for GRP sprite structure.

BroodWar.mpq stores all 234 entries in the clear, so those can be inspected
without any decryption. A StarCraft GRP begins with:
    uint16 frameCount, uint16 maxWidth, uint16 maxHeight
followed by frameCount 8-byte frame headers (x, y, w-1, h-1, uint32 offset).
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def looks_like_grp(data):
    if len(data) < 6 + 8:
        return None
    frames, w, h = struct.unpack_from("<HHH", data, 0)
    if not (1 <= frames <= 4000):
        return None
    if not (1 <= w <= 512 and 1 <= h <= 512):
        return None
    if 6 + frames * 8 > len(data):
        return None
    offs = []
    for i in range(frames):
        x, y, fw, fh, off = struct.unpack_from("<BBBB I".replace(" ", ""), data, 6 + i * 8)
        if fw == 0 or fh == 0 or fw > 255 or fh > 255:
            return None
        if off >= len(data):
            return None
        offs.append(off)
    if any(offs[i] > offs[i + 1] for i in range(len(offs) - 1)):
        return None
    return dict(frames=frames, w=w, h=h, first_off=offs[0])


def classify(head, data):
    if data[:4] == b"RIFF":
        return "WAV"
    if data[:4] in (b"SMK2", b"SMK4"):
        return "SMACKER"
    if data[:4] == b"FORM":
        return "IFF"
    if head[0] == 0x0A or data[:3] == b"PCX":
        return "PCX"
    g = looks_like_grp(data)
    if g:
        return "GRP"
    return "?"


def main():
    for arc in ("BroodWar.mpq", "StarDat.mpq", "BrooDat.mpq"):
        path = os.path.join(ROOT, arc)
        with MPQ(path) as m:
            print("=" * 74)
            print("%s" % arc)
            counts = {}
            grps = []
            for i, (o, cs, fs, flags, rel) in enumerate(m.block_table):
                if not (flags & M.FLAG_EXISTS):
                    continue
                if flags & M.FLAG_ENCRYPTED:
                    counts["ENCRYPTED(skip)"] = counts.get("ENCRYPTED(skip)", 0) + 1
                    continue
                m.fp.seek(o)
                data = m.fp.read(cs)
                k = classify(data[:16], data)
                counts[k] = counts.get(k, 0) + 1
                if k == "GRP":
                    g = looks_like_grp(data)
                    grps.append((i, o, cs, g))
            print("   %s" % counts)
            print("   GRPs found: %d" % len(grps))
            for i, o, cs, g in grps[:30]:
                print("      blk%-5d size=%-8d frames=%-5d %dx%d"
                      % (i, cs, g["frames"], g["w"], g["h"]))
            print()


if __name__ == "__main__":
    main()

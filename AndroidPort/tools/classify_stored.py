"""Classify the STORED (unencrypted, uncompressed) entries in each archive.

These can be read with no decryption at all, so they are a reliable fallback:
whatever they contain is definitely extractable.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mpq as M  # noqa: E402
from mpq import MPQ  # noqa: E402

ROOT = r"F:\KF\XJZB"


def classify(head):
    if head[:4] == b"RIFF":
        return "WAV"
    if head[:4] == b"SMK2" or head[:4] == b"SMK4":
        return "SMACKER"
    if head[:4] == b"FORM":
        return "IFF"
    if head[:3] == b"PCX" or head[0] == 0x0A:
        return "PCX?"
    if head[:4] == b"MPQ\x1a":
        return "MPQ"
    if head[:2] == b"BM":
        return "BMP"
    if head[:4] == b"\x89PNG":
        return "PNG"
    return "?"


def main():
    for arc in ("StarDat.mpq", "BrooDat.mpq", "BroodWar.mpq", "patch_rt.mpq"):
        path = os.path.join(ROOT, arc)
        if not os.path.exists(path):
            continue
        with MPQ(path) as m:
            stored = [(i, e) for i, e in enumerate(m.block_table)
                      if (e[3] & M.FLAG_EXISTS) and not (e[3] & M.FLAG_ENCRYPTED)]
            print("=" * 70)
            print("%s : %d stored entries of %d" % (arc, len(stored), len(m.block_table)))
            kinds = {}
            samples = []
            for i, (o, cs, fs, flags, rel) in stored:
                m.fp.seek(o)
                head = m.fp.read(16)
                k = classify(head)
                kinds[k] = kinds.get(k, 0) + 1
                samples.append((i, o, cs, fs, k, head))
            print("   kinds: %s" % kinds)
            for i, o, cs, fs, k, head in samples[:25]:
                print("   blk%-5d o=%-9d cs=%-8d fs=%-8d %-8s %s"
                      % (i, o, cs, fs, k, head[:12].hex(" ")))
            print()


if __name__ == "__main__":
    main()

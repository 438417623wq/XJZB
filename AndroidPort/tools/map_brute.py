"""Brute-force inflate at every plausible offset in a map file.

Locates any zlib stream regardless of surrounding framing, and reports what
came out -- so we can see the real payload shape.
"""

import os
import sys
import zlib

ROOT = r"F:\KF\XJZB"


def try_at(blob, i):
    """Attempt several framings starting at or near offset i."""
    for wbits in (15, -15, 47, 31):
        try:
            d = zlib.decompressobj(wbits)
            out = d.decompress(blob[i:])
            out += d.flush()
            if out:
                return out, wbits
        except Exception:
            continue
    return None, None


def main():
    path = os.path.join(ROOT, "maps", "(2)Bottleneck.scm")
    with open(path, "rb") as fp:
        blob = fp.read()
    print("size=%d" % len(blob))

    # 1) inflate at the point we spotted in the hexdump
    for probe in (0xC9A1, 0xC9A2, 0xC9A3, 0xC9A4):
        out, wb = try_at(blob, probe)
        print("probe 0x%X wbits=%s -> %s" % (
            probe, wb, ("%d bytes, head=%r" % (len(out), out[:40])) if out else "fail"))

    # 2) full scan for any offset producing something CHK-like
    print("\nfull scan:")
    best = []
    for i in range(len(blob) - 8):
        if blob[i] != 0x78:
            continue
        out, wb = try_at(blob, i)
        if out and len(out) > 128:
            best.append((len(out), i, wb, out[:8]))
    best.sort(reverse=True)
    print("candidates: %d" % len(best))
    for n, i, wb, head in best[:10]:
        print("   off=0x%-8X len=%-9d wbits=%-3s head=%r" % (i, n, wb, head))

    if best:
        n, i, wb, head = best[0]
        out, _ = try_at(blob, i)
        print("\nBEST payload head: %r" % out[:64])
        print("BEST payload len : %d" % len(out))


if __name__ == "__main__":
    main()

"""Extract scenario.chk from .scm/.scx maps by scanning for zlib sectors.

Map archives store their payload unencrypted as MPQ sectors: a 0x02 type byte
followed by a zlib stream. The CHK itself begins with the chunk tag 'VER ',
which makes a reliable success check.
"""

import os
import sys
import zlib

ROOT = r"F:\KF\XJZB"
MAPDIR = os.path.join(ROOT, "maps")

ZLIB_HEADS = (b"\x02\x78\x9c", b"\x02\x78\x01", b"\x02\x78\xda", b"\x02\x78\x5e")


def try_inflate_at(blob, i):
    """Try to inflate a zlib stream starting at blob[i] (i points at 0x78)."""
    for wbits in (15, -15, 47):
        try:
            d = zlib.decompressobj(wbits)
            out = d.decompress(blob[i:i + 8 * 1024 * 1024])
            out += d.flush()
            if len(out) > 64:
                return out
        except Exception:
            continue
    return None


def extract(path):
    with open(path, "rb") as fp:
        blob = fp.read()

    results = []
    for head in ZLIB_HEADS:
        start = 0
        while True:
            j = blob.find(head, start)
            if j < 0:
                break
            start = j + 1
            out = try_inflate_at(blob, j + 1)
            if out and out[:4] == b"VER ":
                results.append((j, out))
    if not results:
        return None
    # the largest CHK is the real scenario
    results.sort(key=lambda t: -len(t[1]))
    return results[0]


def main():
    maps = []
    for root, _d, files in os.walk(MAPDIR):
        for f in files:
            if f.lower().endswith((".scm", ".scx")):
                maps.append(os.path.join(root, f))
    maps.sort()
    print("maps: %d" % len(maps))

    ok = 0
    for p in maps[:20]:
        rel = os.path.relpath(p, ROOT)
        r = extract(p)
        if r:
            off, chk = r
            ok += 1
            # CHK: VER chunk = tag(4) + size(4) + version(2)
            print("%-50s zlib@%-8d chk=%d bytes  VER=%s"
                  % (rel, off, len(chk), chk[4:8].hex(" ")))
        else:
            print("%-50s NO CHK FOUND" % rel)
    print("\nextracted %d/%d" % (ok, min(20, len(maps))))


if __name__ == "__main__":
    main()

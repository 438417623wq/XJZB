"""v2.11: the repack's iscript.bin has a plausible leading count (0x97e6=38886)
but then zeros, so it is not a plain copy. Scan all three archives for the real
IScript header (u16 headerCount, u16 typeCount, u32 headerOffset, u32 typeOffset)
at any offset, and report every candidate that self-validates:
  * 0 < headerCount < 600, 0 < typeCount < 600
  * headerOffset inside the file, typeOffset inside the file
  * headerCount*2 bytes of header offsets fit inside the file
  * every header offset is < len(data) - typeOffset
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"

for fn in ("StarDat.mpq", "BrooDat.mpq", "patch_rt.mpq"):
    p = os.path.join(ROOT, fn)
    if not os.path.exists(p):
        continue
    ar = sc_archive.Archive(p)
    if not ar.has("scripts\\iscript.bin"):
        ar.close()
        continue
    data, gaps = ar.read_with_gaps("scripts\\iscript.bin")
    print("== %s  %d bytes gaps=%d" % (fn, len(data), len(gaps)))
    nz = sum(1 for b in data if b)
    print("   nonzero bytes: %d (%.1f%%)" % (nz, 100.0 * nz / len(data)))
    # where does the nonzero data live?
    runs = []
    i = 0
    while i < len(data):
        if data[i]:
            j = i
            while j < len(data) and data[j]:
                j += 1
            if j - i > 64:
                runs.append((i, j))
            i = j
        else:
            i += 1
    print("   nonzero runs >64B: %s" % (runs[:8],))

    best = []
    for off in range(0, min(len(data) - 12, 4096)):
        hc, tc, ho, to = struct.unpack_from("<HHII", data, off)
        if not (4 < hc < 600 and 0 < tc < 600):
            continue
        if not (off <= ho < len(data) and off < to <= len(data)):
            continue
        if ho + 2 * hc > len(data):
            continue
        try:
            o = list(struct.unpack_from("<%dH" % hc, data, ho))
        except Exception:
            continue
        if max(o) > len(data) - to:
            continue
        best.append((off, hc, tc, ho, to, max(o)))
    print("   candidate headers: %s" % (best[:6],))
    ar.close()

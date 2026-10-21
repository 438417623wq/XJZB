"""v2.11: locate the iscript.bin TYPE TABLE by matching SCPE block offsets.

StarDat's copy has a flat (u16 iscriptId, u16 offset) table at file offset 0 and
every entry it points at begins with the magic 'SCPE'. patch_rt and BrooDat
start with `e6 97 00 00` instead, so their table is somewhere else -- find it by
scanning for a u16 array whose values equal the SCPE block offsets.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"


def scpe_offsets(data):
    out = []
    i = data.find(b"SCPE")
    while i >= 0:
        out.append(i)
        i = data.find(b"SCPE", i + 1)
    return out


for fn, nm in (("StarDat.mpq", "scripts\\iscript.bin"),
               ("BrooDat.mpq", "scripts\\iscript.bin"),
               ("patch_rt.mpq", "scripts\\iscript.bin"),
               ("BrooDat.mpq", "scripts\\iscriptx.bin")):
    ar = sc_archive.Archive(os.path.join(ROOT, fn))
    if not ar.has(nm):
        ar.close()
        continue
    data, gaps = ar.read_with_gaps(nm)
    n = len(data)
    sc = scpe_offsets(data)
    print()
    print("=== %s %s  bytes=%d gaps=%s  SCPE=%d  first@%s"
          % (fn, nm, n, gaps, len(sc), sc[:6]))
    print("    head:", data[:24].hex(" "))

    # For each candidate table start, read (u16 id, u16 off) pairs and count how
    # many offsets land exactly on an SCPE block.
    scset = set(sc)
    best = []
    for start in range(0, min(4096, n - 8)):
        hits = 0
        k = 0
        o = start
        while o + 4 <= n and k < 60:
            off = struct.unpack_from("<H", data, o + 2)[0]
            if off in scset:
                hits += 1
            o += 4
            k += 1
        if hits >= 8:
            best.append((hits, start))
    best.sort(reverse=True)
    print("    table candidates (hits, offset):", best[:6])
    if best:
        start = best[0][1]
        pairs = []
        o = start
        while o + 4 <= n:
            tid = struct.unpack_from("<H", data, o)[0]
            toff = struct.unpack_from("<H", data, o + 2)[0]
            if toff not in scset:
                break
            pairs.append((tid, toff))
            o += 4
        print("    table@%d pairs=%d ids %s..%s"
              % (start, len(pairs), pairs[0][0] if pairs else "-",
                 pairs[-1][0] if pairs else "-"))
        print("    first 16:", pairs[:16])
        print("    ids sorted?", [p[0] for p in pairs] == sorted(p[0] for p in pairs))
    ar.close()

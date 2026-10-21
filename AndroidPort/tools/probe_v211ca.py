"""v2.11: dump scripts\\iscript.bin (StarDat) raw, to settle its layout.

StarDat's copy begins  c6 00 fc 1c c7 00 9c 1d c8 00 2c 21 ...
Two readings are both self-consistent:
  A) flat (u16 typeId, u16 typeOffset) pairs  -> ids 198,199,200,218,216,...
  B) u16 typeCount=198 then u16 typeOffset[198]
Dump the bytes at the candidate offsets to see which one points at a real
type block (a list of (u16 animId, u16 animOffset) pairs terminated by 0xFFFF).
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
ar = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
data, gaps = ar.read_with_gaps("scripts\\iscript.bin")
n = len(data)
print("bytes=%d gaps=%s" % (n, gaps))

cand = [7420, 7580, 8492, 7950, 7992, 8064, 8068, 8124, 8136, 8184, 8196, 8818]
for off in cand:
    if off + 64 > n:
        continue
    b = data[off:off + 64]
    print()
    print("--- @%d ---" % off)
    print("  hex:", b.hex(" "))
    print("  u16:", list(struct.unpack_from("<32H", data, off)))
    print("  txt:", "".join(chr(c) if 32 <= c < 127 else "." for c in b))

# where are the SCPE blocks?
pos = []
i = data.find(b"SCPE")
while i >= 0 and len(pos) < 12:
    pos.append(i)
    i = data.find(b"SCPE", i + 1)
print()
print("first SCPE at:", pos)

# Reading B: count then offsets
cnt = struct.unpack_from("<H", data, 0)[0]
offs_b = list(struct.unpack_from("<%dH" % cnt, data, 2))
print()
print("reading B: count=%d, offsets min=%d max=%d" % (cnt, min(offs_b), max(offs_b)))
print("  sorted?", offs_b == sorted(offs_b))
print("  first 20:", offs_b[:20])
# Reading A: pairs
pairs = []
o = 0
while o + 4 <= n and len(pairs) < cnt:
    pairs.append((struct.unpack_from("<H", data, o)[0],
                  struct.unpack_from("<H", data, o + 2)[0]))
    o += 4
print()
print("reading A: pairs=%d ids min=%d max=%d" % (len(pairs),
      min(p[0] for p in pairs), max(p[0] for p in pairs)))
print("  ids sorted?", [p[0] for p in pairs] == sorted(p[0] for p in pairs))
print("  offsets sorted?", [p[1] for p in pairs] == sorted(p[1] for p in pairs))
print("  first 20:", pairs[:20])
print("  type table ends at byte", 4 * len(pairs))
ar.close()

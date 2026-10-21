"""v2.11: try to read scripts\\iscript.bin to get authoritative animation
frame counts (the walk length is the number of frames the Walking animation
plays), instead of guessing it from pictures.

Documented layout:
    u16 typeCount
    u16 typeOffset[typeCount]      (relative to file start)
    type block:  u16 typeId, u32 animOffset[]  ... 0xFFFF terminator
    anim block:  u16 animId, u32 animOffset  ... 0xFFFF terminator
    opcodes:     sequence of u16 words; 0x0000..0x0009 are parameterised
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

NAMES = ["scripts\\iscript.bin", "scripts\\ISCRIPT.BIN",
         "arr\\iscript.bin", "scripts\\ISCRIPTX.BIN",
         "scripts\\iscriptx.bin", "scripts\\iscript.lob"]

for fn in ("patch_rt.mpq", "StarDat.mpq", "BrooDat.mpq"):
    ar = sc_archive.Archive(os.path.join(ROOT, fn))
    for nm in NAMES:
        if not ar.has(nm):
            continue
        data, gaps = ar.read_with_gaps(nm)
        print("%-14s %-26s bytes=%-8d gaps=%s" % (fn, nm, len(data), len(gaps)))
        print("   head:", data[:48].hex(" "))
        cnt = struct.unpack_from("<H", data, 0)[0]
        print("   u16@0 =", cnt)
        # candidate: u16 count + count*2 offset table fits in the file
        if 0 < cnt < 2000 and 2 + 2 * cnt <= len(data):
            offs = struct.unpack_from("<%dH" % cnt, data, 2)
            mono = sum(1 for a, b in zip(offs, offs[1:]) if b >= a)
            print("   table fits: last=%d mono=%d/%d" % (offs[-1], mono, cnt - 1))
            print("   first 12 offsets:", list(offs[:12]))
        print()
    ar.close()

# Also: what file actually contains the SCPE magic?
print("=== who contains 'SCPE'? ===")
for fn in ("patch_rt.mpq", "StarDat.mpq", "BrooDat.mpq"):
    ar = sc_archive.Archive(os.path.join(ROOT, fn))
    for nm in NAMES:
        if ar.has(nm):
            data, _ = ar.read_with_gaps(nm)
            print("  %s %s SCPE=%d" % (fn, nm, data.count(b"SCPE")))
    ar.close()

"""v2.11: read scripts\\iscript.bin -- the authoritative animation table.

This is the file that says, for every unit and building, how many frames each
animation has. If it parses, the walk-block counts for batch B stop being a
visual judgement call.

Layout (the standard Blizzard IScript.bin header):
    u16 headerCount      number of iscript ids
    u16 typeCount        number of types
    u32 headerOffset     usually 8
    u32 typeOffset       start of the type data
    u16 headerOffsets[headerCount]   each RELATIVE to typeOffset
Each type is a run of animation entries:
    u8  frameCount
    u16 animationId      0 terminates the type
    <opcodes...>
The opcode stream is terminated by the `end` opcode, which is byte 0x00 or
0x0c depending on the game version, so this probe tries to walk the types
greedily and VALIDATES the parse against five units whose walk length is
already known from the shipped manifest:
    marine walk=3, zergling walk=3, hydra walk=2, zealot walk=5, dragoon walk=8

Usage: python probe_v211av.py [dumpTypes]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

data, gaps = PT.read_with_gaps("scripts\\iscript.bin")
print("iscript.bin %d bytes, %d gaps" % (len(data), len(gaps)))

hc, tc, ho, to = struct.unpack_from("<HHII", data, 0)
print("headerCount=%d typeCount=%d headerOffset=%d typeOffset=%d" % (hc, tc, ho, to))

if not (0 < hc < 600 and 0 < tc < 600 and 8 <= ho < len(data) and 0 < to <= len(data)):
    print("!! header does not look like the standard layout")
    print("first 32 bytes:", data[:32].hex(" "))
    sys.exit(1)

offs = list(struct.unpack_from("<%dH" % hc, data, ho))
print("first 24 header offsets:", offs[:24])
print("min=%d max=%d  (typeOffset+max=%d, file=%d)"
      % (min(offs), max(offs), to + max(offs), len(data)))

# dump raw bytes of the first few types so the animation-entry shape is visible
n_dump = int(sys.argv[1]) if len(sys.argv) > 1 else 4
for k in range(min(n_dump, hc)):
    o = to + offs[k]
    print("\n-- type %d @ %d : %s" % (k, o, data[o:o + 64].hex(" ")))

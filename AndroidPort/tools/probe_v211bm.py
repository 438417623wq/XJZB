"""v2.11: iscript.bin structural probe, take 2.

Earlier attempts (probe_v211av/aw) assumed the classic layout
    u16 headerCount, u16 typeCount, u32 headerOffset, u32 typeOffset
and found nothing.  New hypothesis, from the observed byte pattern:

    patch_rt\\scripts\\iscript.bin  (40482 bytes)
      u32 @0            = 0x000097e6 = 38886   <-- offset of a u32 table
      0x0000..0x055b    = zeros (1372 bytes)
      0x055c (1372)     = first 'SCPE' magic block
      38886..40482      = 1596 bytes = 399 * 4  <-- the offset table

So: the table at (u32@0) holds one u32 offset per iscript entry, and the entry
count is implied by the file end.  Each entry points at an 'SCPE' block.

This script tests that hypothesis on all three archives and, if it holds,
decodes the iscript opcode stream of an entry into a frame-index list so the
walk / attack / death frame counts become ground truth instead of eyeballed.

Usage: python probe_v211bm.py [archive] [entry]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
ARCHIVES = {
    "PT": os.path.join(ROOT, "patch_rt.mpq"),
    "SD": os.path.join(ROOT, "StarDat.mpq"),
    "BD": os.path.join(ROOT, "BrooDat.mpq"),
}
NAME = "scripts\\iscript.bin"

tags = [sys.argv[1].upper()] if len(sys.argv) > 1 else ["PT", "SD", "BD"]
for tag in tags:
    ar = sc_archive.Archive(ARCHIVES[tag])
    if not ar.has(NAME):
        print("%s: MISS" % tag)
        continue
    data, gaps = ar.read_with_gaps(NAME)
    n = len(data)
    head = struct.unpack_from("<I", data, 0)[0]
    print("=== %s  size=%d  u32@0=%d  (fileSize-u32@0)=%d  /4=%s"
          % (tag, n, head, n - head, (n - head) / 4.0))

    # candidate table start = u32@0
    for tstart in (head,):
        if not (0 < tstart < n):
            continue
        cnt = (n - tstart) // 4
        offs = list(struct.unpack_from("<%dI" % cnt, data, tstart))
        inrange = sum(1 for o in offs if 0 < o < n)
        scpe = sum(1 for o in offs if 0 < o < n - 4 and data[o:o + 4] == b"SCPE")
        print("   table@%d entries=%d inrange=%d scpe=%d" % (tstart, cnt, inrange, scpe))
        print("   first8=%s" % (offs[:8],))
        if scpe > cnt * 0.5:
            print("   *** HYPOTHESIS HOLDS ***")
            for i in (0, 1, 2, 3, 40, 100, 200, 300, 397, 398):
                if i >= cnt:
                    continue
                o = offs[i]
                if not (0 < o < n - 4):
                    continue
                ln = (offs[i + 1] - o) if (i + 1 < cnt and offs[i + 1] > o) else (n - o)
                print("     [%3d] @%-6d len=%-5d %s" % (i, o, ln, data[o:o + 16].hex()))
    ar.close()

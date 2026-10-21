"""v2.10: why do some sfx table names lose their first character?

The parsed table shows 'orsair\\PCoRdy00.wav' and no Dark Archon entries at all,
while the MPQ listfile clearly has both. Either the offset table wraps past
64KB or the strings are stored with a prefix trick. Dump the raw region so the
lookup rule in pipeline_sounds.py can be fixed instead of guessed at.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))

data = SD.read("arr\\sfxdata.tbl")
n, = struct.unpack_from("<H", data, 0)
print("entries=%d  table_bytes=%d  u16_offset_span=%d" % (n, len(data), 2 + 2 * n))
offs = struct.unpack_from("<%dH" % n, data, 2)
print("max offset=%d  (u16 overflow threshold 65535)" % max(offs))

# show the neighbourhood of the corsair entries
for i, o in enumerate(offs):
    end = data.find(b"\0", o)
    s = data[o:end]
    if b"orsair" in s or b"Rdy00" in s and b"Co" in s:
        print("idx=%-5d off=%-6d prev_off=%-6d raw=%r" %
              (i, o, offs[i - 1] if i else -1, data[max(0, o - 12):end + 4]))
        if i > 400:
            break

print("--- bytes 0..80:", data[:80])
print("--- first 6 strings:")
for i in range(6):
    end = data.find(b"\0", offs[i])
    print("   %d off=%d %r" % (i, offs[i], data[offs[i]:end]))

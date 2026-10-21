"""v2.10: confirm that basename hashing rescues the truncated table names.

BD's table stores the Corsair group as 'orsair\\PCoRdy00.wav' -- the leading 'c'
is gone. sc_archive hashes only the bare filename, so 'sound/orsair/PCoRdy00.wav'
may still resolve. Test that, and print the complete Corsair / ARCHON groups so
the Dark Archon voice (which is filed under ARCHON with a PDa prefix) is picked
by exact name.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))


def parse_tbl(data):
    n, = struct.unpack_from("<H", data, 0)
    offs = struct.unpack_from("<%dH" % n, data, 2)
    return [data[offs[i]:data.find(b"\0", offs[i])].decode("latin1")
            for i in range(n)]


bd = parse_tbl(BD.read("arr\\sfxdata.tbl"))
print("--- BD groups:")
for probe in ("orsair", "ARCHON"):
    print("  %s:" % probe)
    for s in bd:
        if probe.lower() in s.lower():
            print("     ", s)

print("--- basename resolution test:")
for nm in ("sound/orsair/PCoRdy00.wav", "sound/Protoss/ZEALOT/PZeRdy00.WAV",
           "sound/ARCHON/PDaRdy00.WAV"):
    for tag, ar in (("SD", SD), ("BD", BD)):
        if ar.has(nm):
            d, gaps = ar.read_with_gaps(nm)
            print("  %s %-34s size=%-7d riff=%s" % (tag, nm, len(d), d[:4] == b"RIFF"))
            break
    else:
        print("  -- %-34s NOT FOUND" % nm)

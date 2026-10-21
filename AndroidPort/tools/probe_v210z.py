"""v2.10: confirm the Corsair / Dark Archon voices are readable by real path.

The sfx table stores them truncated ('orsair\\PCoRdy00.wav',
'ARCHON\\PDaRdy00.WAV') and those names do not resolve. The listfile has the
true paths, so read those directly -- if they work, pipeline_sounds.py only
needs a direct-path escape hatch for the handful of broken table entries.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

PATHS = [
    "sound/protoss/corsair/pcordy00.wav",
    "sound/protoss/corsair/pcowht00.wav",
    "sound/protoss/corsair/pcoyes00.wav",
    "sound/protoss/corsair/pcopss00.wav",
    "sound/protoss/darchon/pdardy00.wav",
    "sound/protoss/darchon/pdawht00.wav",
    "sound/protoss/darchon/pdayes00.wav",
    "sound/protoss/darktemplar/pdtdth00.wav",
]

for nm in PATHS:
    found = False
    for tag, ar in (("SD", SD), ("BD", BD)):
        if ar.has(nm):
            d, gaps = ar.read_with_gaps(nm)
            print("%s %-42s size=%-7d riff=%s" % (tag, nm, len(d), d[:4] == b"RIFF"))
            found = True
            break
    if not found:
        print("-- %-42s NOT FOUND" % nm)

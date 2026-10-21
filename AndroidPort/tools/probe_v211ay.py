"""v2.11: is BroodWar.mpq a PRISTINE archive? The other three (StarDat, BrooDat,
patch_rt) are a warez repack whose units.dat / images.dat / iscript.bin are all
unparseable. If BroodWar.mpq is untouched, its iscript.bin gives the real
animation frame counts for every unit -- which is exactly what batch B needs.

Also checks whether the repack's iscript.bin is even iscript: the real file is a
binary opcode stream with no ASCII in it, whereas this one carries 398 "SCPE"
chunks.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
BW = os.path.join(ROOT, "BroodWar.mpq")
print("BroodWar.mpq", os.path.getsize(BW), "bytes")
ar = sc_archive.Archive(BW)

print("listfile:", ar.has("(listfile)"))
if ar.has("(listfile)"):
    lf, _ = ar.read_with_gaps("(listfile)")
    names = [n for n in lf.decode("latin-1").split("\r\n") if n]
    print("  %d entries" % len(names))
    for want in ("iscript", "images.dat", "units.dat", "sprites.dat", "ultra",
                 "ultralisk"):
        hits = [n for n in names if want.lower() in n.lower()]
        print("  %-12s -> %s" % (want, hits[:6]))

print()
for cand in ("scripts\\iscript.bin", "arr\\iscript.bin", "arr\\images.dat",
             "arr\\units.dat", "arr\\sprites.dat", "unit\\zerg\\ultra.grp",
             "unit\\zerg\\Snakey.grp", "unit\\zerg\\chrysal.grp"):
    try:
        ok = ar.has(cand)
    except Exception as e:
        ok = "ERR"
    if ok:
        d, g = ar.read_with_gaps(cand)
        head = d[:24].hex(" ")
        print("HIT %-28s %8d bytes gaps=%-3d head=%s" % (cand, len(d), len(g), head))
        if cand.endswith("iscript.bin"):
            hc, tc, ho, to = struct.unpack_from("<HHII", d, 0)
            print("     headerCount=%d typeCount=%d headerOffset=%d typeOffset=%d"
                  % (hc, tc, ho, to))
    else:
        print("--- %s" % cand)
ar.close()

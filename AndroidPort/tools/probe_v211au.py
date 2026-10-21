"""v2.11: is there an iscript/scripts file in the repack? That would give the
animation frame counts authoritatively instead of reading them off pictures.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
for fn in ("StarDat.mpq", "BrooDat.mpq", "patch_rt.mpq"):
    p = os.path.join(ROOT, fn)
    if not os.path.exists(p):
        print("no file", p)
        continue
    ar = sc_archive.Archive(p)
    print("==", fn)
    for cand in ("arr\\iscript.bin", "scripts\\iscript.bin", "iscript.bin",
                 "arr\\scripts.bin", "scripts.bin", "arr\\images.tbl"):
        try:
            ok = ar.has(cand)
        except Exception as e:
            ok = "ERR %s" % e
        if ok:
            try:
                d, g = ar.read_with_gaps(cand)
                print("   HIT %-24s %d bytes gaps=%d" % (cand, len(d), len(g)))
            except Exception as e:
                print("   HIT %-24s read failed %s" % (cand, e))
        else:
            print("   --- %s" % cand)
    ar.close()

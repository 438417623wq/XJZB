"""v2.11: align the ImageTypes enum against arr\\images.tbl by GRP sequence.

The repack's images.tbl interleaves the LO files (`.lof/.lou/.lod/.los`) with
the GRPs, and drops some rows, so raw index != image id. But the ORDER is
preserved: dropping every non-.grp row yields exactly the enum's main-image
sequence. This prints both sequences side by side so the pairing can be read
off directly, with no guessing.

Usage: python probe_v211am.py [lo] [hi]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

ENUM_TXT = os.path.join(
    r"C:\Users\XiaoXin\AppData\Local\Temp\dsh-spill-y8WfPh\session-cb4a4d09e0b0",
    "254abc3c9a02-web_fetch.txt")

lo = int(sys.argv[1]) if len(sys.argv) > 1 else 0
hi = int(sys.argv[2]) if len(sys.argv) > 2 else 130


def enum_names():
    txt = open(ENUM_TXT, encoding="utf8", errors="replace").read()
    i = txt.find("enum struct ImageTypes")
    j = txt.find("enum struct Sounds", i)
    return re.findall(r"IMAGEID_([A-Za-z0-9_]+)", txt[i:j])


def tbl(path, ar):
    data, _ = ar.read_with_gaps(path)
    cnt = data[0] | (data[1] << 8)
    offs = [data[2 + 2 * k] | (data[3 + 2 * k] << 8) for k in range(cnt)]
    return [data[o:data.index(b"\x00", o)].decode("cp1252", "replace") for o in offs]


names = enum_names()
ents = tbl("arr\\images.tbl", SD)
grps = [(i, e) for i, e in enumerate(ents) if e.lower().endswith(".grp")]
mains = [(i, n) for i, n in enumerate(names)
         if not n.endswith("_Shadow") and n != "None"]

print("table rows=%d grp rows=%d | enum names=%d main=%d"
      % (len(ents), len(grps), len(names), len(mains)))
print()
for k in range(lo, min(hi, max(len(grps), len(mains)))):
    g = grps[k] if k < len(grps) else None
    m = mains[k] if k < len(mains) else None
    print("  #%-4d %-40s | tbl%-4s %s"
          % (k, m[1] if m else "-", g[0] if g else "-", g[1] if g else "-"))

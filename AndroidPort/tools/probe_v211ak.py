"""v2.11: join the authoritative ImageTypes enum against arr\\images.tbl.

The ImageTypes enum (bwenums.h) is the real images.dat row order, and
images.tbl is indexed by exactly that row number. Joining them names every GRP
in the archive without any guessing, which is what the four failed
icon-silhouette probes (v211q/r/t/z/aa) could never do.

Usage: python probe_v211ak.py [lo] [hi]
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

lo = int(sys.argv[1]) if len(sys.argv) > 1 else 55
hi = int(sys.argv[2]) if len(sys.argv) > 2 else 115


def enum_names():
    txt = open(ENUM_TXT, encoding="utf8", errors="replace").read()
    i = txt.find("enum struct ImageTypes")
    j = txt.find("enum struct Sounds", i)
    return re.findall(r"IMAGEID_([A-Za-z0-9_]+)", txt[i:j])


def tbl(path):
    """Return the entry list of a TBL file."""
    for ar, tag in ((SD, "SD"), (BD, "BD")):
        if ar.has(path):
            data, _ = ar.read_with_gaps(path)
            cnt = data[0] | (data[1] << 8)
            offs = [data[2 + 2 * k] | (data[3 + 2 * k] << 8) for k in range(cnt)]
            out = []
            for o in offs:
                e = data.index(b"\x00", o)
                out.append(data[o:e].decode("cp1252", "replace"))
            return out, tag
    return None, None


names = enum_names()
print("enum names: %d" % len(names))
for arch, tag in ((SD, "StarDat"), (BD, "BrooDat")):
    ents, t = tbl("arr\\images.tbl")
    if ents is None:
        print("== %s: no images.tbl" % arch)
        continue
    print("== %s images.tbl entries=%d" % (arch, len(ents)))
    for i in range(lo, min(hi, len(ents))):
        nm = names[i] if i < len(names) else "?"
        print("  %4d  %-38s %s" % (i, nm, ents[i]))

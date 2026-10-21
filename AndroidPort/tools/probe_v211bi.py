"""v2.11: decode the LO files -- the authoritative animation layout.

Each image in arr\\images.tbl has a companion LO row (.lof/.log/.lou/.lod/.lol/
.los/.lob/.loa/.loo/.lox). In StarCraft the LO file is what maps a GRP's frames
into named animations, so it is the authority for "how long is the walk cycle".

Header (established from the dumps in probe_v211bh.py):
    u32 count            number of entries  (== the GRP frame count, usually)
    u32 unk              small; 1 for .log, 0x16=22 for .lof/.lou/.lod
    u32 offsets[count]   absolute file offsets; offsets[0] == 8 + 4*count
    u8  data[]           one variable-length entry per frame

This probe dumps the entry bytes so the entry grammar can be read off, and
cross-checks count against the GRP frame count for a set of known units.

Usage: python probe_v211bi.py
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

WANT = [
    ("marine", "terran\\marine.grp", "terran\\marine.log"),
    ("zergling", "zerg\\zergling.grp", "zerg\\zergling.log"),
    ("hydra", "zerg\\hydra.grp", "zerg\\hydra.log"),
    ("zealot", "protoss\\zealot.grp", "protoss\\zealot.log"),
    ("dragoon", "protoss\\dragoon.grp", "protoss\\dragoon.log"),
    ("ultra", "zerg\\ultra.grp", "zerg\\ultra.log"),
    ("queen", "zerg\\queen.grp", "zerg\\queen.log"),
    ("defiler", "zerg\\defiler.grp", "zerg\\defiler.log"),
    ("guardian", "zerg\\guardian.grp", "zerg\\guardian.log"),
    ("devourer", "zerg\\devour.grp", "zerg\\devour.log"),
    ("medic", "terran\\medic.grp", "terran\\medic.log"),
    ("valkyrie", "terran\\bomber.grp", "terran\\bomber.log"),
    ("spider", "terran\\Spider.grp", "terran\\Spider.log"),
    ("control", "terran\\control.grp", "terran\\control.lof"),
]


def load(name):
    for ar in (PT, SD, BD):
        for pre in ("unit\\", ""):
            try:
                if ar.has(pre + name):
                    d, g = ar.read_with_gaps(pre + name)
                    return d, g, pre + name
            except Exception:
                pass
    return None, None, None


def parse_lo(d):
    count, unk = struct.unpack_from("<II", d, 0)
    offs = list(struct.unpack_from("<%dI" % count, d, 8))
    return count, unk, offs


for key, grpname, loname in WANT:
    gd, _, gpath = load(grpname)
    ld, lg, lpath = load(loname)
    nfr = None
    if gd is not None:
        fr, mw, mh = grpm.decode_grp(gd, ())
        nfr = len(fr)
    print("== %-10s grp=%-4s lo=%-4s (%s)"
          % (key, nfr, (len(ld) if ld else "MISS"), loname))
    if ld is None:
        continue
    count, unk, offs = parse_lo(ld)
    print("   count=%-4d unk=%-4d offs[0]=%-6d offs[-1]=%-6d file=%d"
          % (count, unk, offs[0], offs[-1], len(ld)))
    sizes = [offs[i + 1] - offs[i] for i in range(count - 1)]
    sizes.append(len(ld) - offs[-1])
    uniq = sorted(set(sizes))
    print("   entry sizes: min=%d max=%d distinct=%s"
          % (min(sizes), max(sizes), uniq[:12]))
    for i in range(min(6, count)):
        e = ld[offs[i]:offs[i + 1] if i + 1 < count else len(ld)]
        print("     f%-3d (%3d B) %s" % (i, len(e), e[:40].hex(" ")))

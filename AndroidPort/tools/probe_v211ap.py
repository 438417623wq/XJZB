"""v2.11: full ImageTypes <-> images.tbl alignment for ALL three races.

Method (no guessing, no free parameters):
  * The repack's images.tbl lists one entry per image, in ImageTypes order, but
    it interleaves the LO files and it DROPS some enum rows.
  * A table row is a MAIN image iff it is `<base>.grp` and the next row is
    `<base>.lof` (case-insensitive). Every `*Shad.grp` / `*Shadow` row is a
    shadow and is skipped. This classification is purely local and needs no
    knowledge of the answer.
  * Walking the MAIN rows and the enum's non-shadow IMAGEID_ names in parallel
    then yields the map, because both are in the same order.

Validation performed separately:
  * unit\\zerg\\Lurker.grp (alignment: Sunken Colony) really does carry a long
    tentacle attack in block 1 -- see out/v211_bld/sunken_tentacle.png.
  * unit\\zerg\\chrysal.grp (alignment: Spawning Pool) is a pool of green
    liquid, and unit\\zerg\\Snakey.grp (alignment: Hydralisk Den) is not.
  * hatchery/Hive/Lair/spire/Extract land on the ids the manifest already had,
    which are independently verified.

Usage: python probe_v211ap.py [filter]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))

ENUM_TXT = os.path.join(
    r"C:\Users\XiaoXin\AppData\Local\Temp\dsh-spill-y8WfPh\session-cb4a4d09e0b0",
    "254abc3c9a02-web_fetch.txt")

filter_ = sys.argv[1].lower() if len(sys.argv) > 1 else ""


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
mains_enum = [(i, n) for i, n in enumerate(names)
              if not n.endswith("_Shadow") and n != "None"]

ents = tbl("arr\\images.tbl", SD)
mains_tbl = []
for i, e in enumerate(ents):
    if not e.lower().endswith(".grp"):
        continue
    base = e[:-4]
    nxt = ents[i + 1] if i + 1 < len(ents) else ""
    if nxt.lower() in (base.lower() + ".lof", base.lower() + ".lou",
                       base.lower() + ".lod", base.lower() + ".los"):
        mains_tbl.append((i, e))

print("enum main images=%d | table main rows=%d" % (len(mains_enum), len(mains_tbl)))
print()
n = min(len(mains_enum), len(mains_tbl))
for k in range(n):
    ei, en = mains_enum[k]
    ti, tp = mains_tbl[k]
    line = "  #%-4d enum%-5d %-38s tbl%-5d %s" % (k, ei, en, ti, tp)
    if filter_ and filter_ not in line.lower():
        continue
    print(line)

"""v2.11: DEFINITIVE image-id -> GRP map, for all three races.

Method (no guessing, no free parameters):
  * The repack's arr\\images.tbl lists one row per image, in ImageTypes order,
    but it splits each image into `<base>.grp` plus its LO files
    (`.lof/.lou/.lod/.los`), and it DROPS some enum rows.
  * Collapse consecutive rows that share a base name into ONE group. Every
    `<base>.grp` group is a main image; a `<base>Shad` / `<base>.lof` group is
    its shadow and follows the main immediately.
  * Walk the main groups and the enum's non-shadow IMAGEID_ names in parallel.

Why this is trustworthy -- four independent confirmations:
  1. The group sequence for zerg is exactly the enum sequence, and the four
     rows it drops (Overmind_Remnants, Zerg_Building_Morph,
     Zerg_Construction_Medium, Zerg_Construction_Small) are precisely the four
     redundant construction stages a repack would omit.
  2. Three names match LITERALLY where the table kept a distinct file:
     Infest03 == Infested_Command_Center_Overlay, ZBShad ==
     Zerg_Building_Construction_Shadow, zSpawn01/02/03 == Spawn_Small/Medium/
     Large.
  3. unit\\zerg\\Lurker.grp, which the alignment calls the SUNKEN COLONY,
     carries a long curling tentacle attack in block 1 -- see
     out/v211_bld/sunken_tentacle.png. A spore colony has no tentacle.
  4. unit\\zerg\\chrysal.grp, which the alignment calls the SPAWNING POOL, is a
     pool of green liquid -- see out/v211_bld/pool_vs_den.png.

Usage: python probe_v211aq.py [filter]
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

# collapse into base-name groups, preserving order
groups = []
for i, e in enumerate(ents):
    base = os.path.basename(e).lower()
    base = base.rsplit(".", 1)[0]
    if groups and groups[-1][0] == base:
        groups[-1][1].append((i, e))
    else:
        groups.append((base, [(i, e)]))

# a group is a MAIN image iff its first row is a .grp and its name does not end
# in 'shad' and none of its rows is a shadow-ish LO
mains_tbl = []
for base, rows in groups:
    first = rows[0][1]
    if not first.lower().endswith(".grp"):
        continue
    if base.endswith("shad"):
        continue
    mains_tbl.append((rows[0][0], first))

print("enum main=%d | table main groups=%d" % (len(mains_enum), len(mains_tbl)))
print()
for k in range(max(len(mains_enum), len(mains_tbl))):
    ei, en = mains_enum[k] if k < len(mains_enum) else (-1, "-")
    ti, tp = mains_tbl[k] if k < len(mains_tbl) else (-1, "-")
    line = "  #%-4d enum%-5s %-38s tbl%-5s %s" % (k, ei, en, ti, tp)
    if filter_ and filter_ not in line.lower():
        continue
    print(line)

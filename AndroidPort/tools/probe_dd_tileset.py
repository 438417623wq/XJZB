"""Test whether CHK DD2's doodadType is a per-tileset index.

The DD2 type is definitely NOT a global images.tbl index (id 256 on
bloodbath resolves to terran\\ttaShad.grp).  StarCraft keeps doodads in a
per-tileset table, so the likely meaning is: index into the ordered list of
`thingy\\tileset\\<Tileset>\\` entries for the map's own tileset.

This probe builds that per-tileset list from images_tbl2 (images.tbl order),
then for every bundled map prints the tileset, the DD2 id range, and whether
each id lands inside the list.  If every id is in range and the implied
names look like scenery, the hypothesis holds and batch D can ship.

Usage:
    python probe_dd_tileset.py
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pipeline_maps as pm

TBL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images_tbl2.txt")

rows = []
for line in open(TBL, encoding="utf8"):
    idx, name = line.rstrip("\n").split("\t")
    rows.append((int(idx), name))

# group thingy\tileset\<Dir>\<File>.grp by directory, preserving images.tbl order
per_ts = collections.OrderedDict()
for i, n in rows:
    low = n.lower()
    if not low.startswith("thingy\\tileset\\"):
        continue
    parts = n.split("\\")
    if len(parts) < 4:
        continue
    d = parts[2].lower()
    per_ts.setdefault(d, []).append((i, parts[3]))

print("per-tileset doodad counts (images.tbl order):")
for d, lst in per_ts.items():
    print(f"  {d:12s} {len(lst):3d}  {[f for _, f in lst][:8]}")

MAPS = [
    ("maps\\(4)Blood Bath.scm", "bloodbath"),
    ("maps\\(2)Bottleneck.scm", "bottleneck"),
    ("maps\\(2)Boxer.scm", "boxer"),
    ("maps\\(8)The Hunters.scm", "hunters"),
    ("maps\\(4)Dark Crystal.scm", "darkcrystal"),
    ("maps\\(3)Three Kingdoms.scm", "3kingdoms"),
    ("maps\\(2)The Small Divide.scm", "divide"),
    ("maps\\(4)Cyclone.scm", "cyclone"),
    ("maps\\(2)Volcanis.scm", "volcanis"),
    ("maps\\(2)River Crossing.scm", "river"),
]

print("\nper-map DD2 id range vs its own tileset's doodad list:")
for src, mid in MAPS:
    r = pm.read_chk(os.path.join(pm.ROOT, src))
    if not r:
        continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    if b"DD2 " not in sec or b"ERA " not in sec:
        continue
    off_era, _ = sec[b"ERA "]
    tname = pm.TILESETS.get(g.byte(off_era), "?")
    lst = per_ts.get(tname.lower(), [])
    off, size = sec[b"DD2 "]
    n = size // 8
    ids = [g.u16(off + i * 8) for i in range(n)]
    if not ids:
        print(f"  {mid:12s} ts={tname:9s} DD2 empty")
        continue
    inrange = [i for i in ids if i < len(lst)]
    over = sorted({i for i in ids if i >= len(lst)})
    print(f"  {mid:12s} ts={tname:9s} list={len(lst):3d} ids {min(ids)}..{max(ids)} "
          f"in-range={len(inrange)}/{n} over={over[:12]}")
    # what the low ids resolve to
    shown = sorted({i for i in ids if i < len(lst)})[:10]
    print(f"      resolves: {[(i, lst[i][1]) for i in shown]}")

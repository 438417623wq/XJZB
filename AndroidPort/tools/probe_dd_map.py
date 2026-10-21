"""Test whether the CHK DD2 doodad id indexes images.tbl.

The maps' DD2 ids run 0..287 while only 25 of the 160 extracted doodad PNGs
got numeric `ddNNN` names (those are images.tbl indices whose filename the
repack's byte gaps destroyed).  The real doodad art lives at
`unit\\thingy\\tileset\\<Tileset>\\<Name>.grp` and shows up in images_tbl2 as
`thingy\\tileset\\...`.

This probe prints:
  1. the index range and count of every `thingy\\tileset\\` entry, and
  2. what images_tbl2 holds at the ids each map actually uses,
so we can tell at a glance whether ddID is an images.tbl index (contiguous
doodad block) or an independent exe-side doodad table (no correlation).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TBL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images_tbl2.txt")

rows = []
for line in open(TBL, encoding="utf8"):
    idx, name = line.rstrip("\n").split("\t")
    rows.append((int(idx), name))

thingy = [(i, n) for i, n in rows if n.lower().startswith("thingy\\tileset\\")]
print(f"images_tbl2 rows={len(rows)}  thingy\\tileset entries={len(thingy)}")
if thingy:
    idxs = [i for i, _ in thingy]
    print(f"index range {min(idxs)}..{max(idxs)}  contiguous={max(idxs)-min(idxs)+1 == len(idxs)}")
    gaps = sorted(set(range(min(idxs), max(idxs) + 1)) - set(idxs))
    print(f"gaps inside range: {len(gaps)} {gaps[:20]}")
    print("first 10:")
    for i, n in thingy[:10]:
        print(f"   {i:4d} {n}")
    print("last 5:")
    for i, n in thingy[-5:]:
        print(f"   {i:4d} {n}")

by_idx = dict(rows)
USED = {
    "bloodbath": [256, 257, 137],
    "bottleneck": [241, 105, 106, 112, 71, 104, 70, 63, 64, 154],
    "darkcrystal": [126, 45, 46, 123, 124, 122, 127, 30, 141, 17],
    "divide": [35, 253, 254, 255, 100, 101, 105, 108, 114, 117],
    "volcanis": [21, 4, 3, 0, 1, 19, 2, 25, 9, 11],
    "cyclone": [62, 79, 80, 89, 73, 103, 87, 45, 61, 65],
    "3kingdoms": [91, 106, 95, 96, 103, 107, 200, 202, 287, 88],
    "river": [185, 187, 186, 182, 180, 181, 183, 98, 96, 255],
}
print("\nimages_tbl2 lookup at the ids each map uses:")
for mid, ids in USED.items():
    print(f"  {mid}:")
    for i in ids:
        n = by_idx.get(i)
        mark = "DOODAD" if (n or "").lower().startswith("thingy\\tileset\\") else ""
        print(f"     {i:4d} -> {n!r} {mark}")

"""v2.23: add elev.bin + meta flags to every shipped map, and build the island maps.

Terrain art is never re-rendered -- see pipeline_maps.add_elevation. Island
maps are built once (they have no shipped art yet) and then slimmed.
"""
import os, sys
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

LEGACY = [
    (r"maps\(4)Blood Bath.scm", "bloodbath"),
    (r"maps\(2)Bottleneck.scm", "bottleneck"),
    (r"maps\(2)Boxer.scm", "boxer"),
    (r"maps\(8)The Hunters.scm", "hunters"),
    (r"maps\(4)Dark Crystal.scm", "darkcrystal"),
    (r"maps\(2)River Crossing.scm", "river"),
    (r"maps\(3)Three Kingdoms.scm", "3kingdoms"),
    (r"maps\(2)The Small Divide.scm", "divide"),
    (r"maps\(4)Cyclone.scm", "cyclone"),
    (r"maps\(2)Volcanis.scm", "volcanis"),
]

maps_dir = os.path.join(pm.OUT, "maps")
shipped = sorted(d for d in os.listdir(maps_dir)
                 if os.path.isdir(os.path.join(maps_dir, d)))
src_by_id = {m: s for s, m, _n, _g in pm.MAPS}
for s, m in LEGACY:
    src_by_id[m] = s

NEW_ISLANDS = [m for s, m, _n, g in pm.MAPS if g == "island"]

ok = miss = 0
for mid in shipped:
    src = src_by_id.get(mid)
    if src is None:
        print("no source for", mid); miss += 1; continue
    if pm.add_elevation(src, mid):
        ok += 1
    else:
        print("FAIL", mid); miss += 1

for src, mid, name, group in pm.MAPS:
    if group != "island":
        continue
    if os.path.isdir(os.path.join(maps_dir, mid)):
        print("island already built:", mid); continue
    if pm.build_map(src, mid, name):
        ok += 1
    else:
        print("FAIL island", mid); miss += 1

print("elevation pass: ok=%d fail=%d" % (ok, miss))
pm.write_map_index()
print("index written")

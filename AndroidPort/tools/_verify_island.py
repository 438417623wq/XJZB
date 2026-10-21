import sys, os, json, zipfile, io
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import importlib, pipeline_maps as pm
importlib.reload(pm)

SHIPPED = {mid: src for src, mid, _n, _g in pm.MAPS}
for mid, src in [("bloodbath", r"maps\(4)Blood Bath.scm"),
                 ("bottleneck", r"maps\(2)Bottleneck.scm"),
                 ("boxer", r"maps\(2)Boxer.scm"),
                 ("hunters", r"maps\(8)The Hunters.scm"),
                 ("darkcrystal", r"maps\(4)Dark Crystal.scm"),
                 ("river", r"maps\(2)River Crossing.scm"),
                 ("3kingdoms", r"maps\(3)Three Kingdoms.scm"),
                 ("divide", r"maps\(2)The Small Divide.scm"),
                 ("cyclone", r"maps\(4)Cyclone.scm"),
                 ("volcanis", r"maps\(2)Volcanis.scm")]:
    SHIPPED.setdefault(mid, src)

# baseline island flags from the v2.41 APK
za = zipfile.ZipFile(r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk")
base = {}
for n in za.namelist():
    if n.endswith("/meta.json"):
        mid = n.split("/")[-2]
        base[mid] = json.loads(za.read(n)).get("island")

bad = 0
print("%-18s %-6s %-6s %-6s %s" % ("map", "v2.41", "census", "now", "match"))
for mid in sorted(SHIPPED):
    c = pm.map_census(SHIPPED[mid])
    if c is None:
        print("%-18s CENSUS-NONE" % mid); bad += 1; continue
    now = 0 if c["connected"] else 1
    b = base.get(mid)
    flag = "ok" if now == b else "*** DIFF ***"
    if now != b: bad += 1
    print("%-18s %-6s %-6s %-6s %s" % (mid, b, 0 if c["connected"] else 1, now, flag))
print("mismatches=%d / %d" % (bad, len(SHIPPED)))

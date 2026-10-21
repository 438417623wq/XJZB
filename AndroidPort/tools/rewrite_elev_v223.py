"""v2.23: rewrite every elev.bin as the 0/1/2 level bitmap (fast path).

The first elevation pass wrote a high/low boolean before the level model was
settled; this only re-derives elev.bin, leaving meta and terrain untouched.
"""
import os, sys
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

LEGACY = {
    "bloodbath": r"maps\(4)Blood Bath.scm",
    "bottleneck": r"maps\(2)Bottleneck.scm",
    "boxer": r"maps\(2)Boxer.scm",
    "hunters": r"maps\(8)The Hunters.scm",
    "darkcrystal": r"maps\(4)Dark Crystal.scm",
    "river": r"maps\(2)River Crossing.scm",
    "3kingdoms": r"maps\(3)Three Kingdoms.scm",
    "divide": r"maps\(2)The Small Divide.scm",
    "cyclone": r"maps\(4)Cyclone.scm",
    "volcanis": r"maps\(2)Volcanis.scm",
}
src_by_id = {m: s for s, m, _n, _g in pm.MAPS}
src_by_id.update(LEGACY)

maps_dir = os.path.join(pm.OUT, "maps")
ok = 0
for mid in sorted(os.listdir(maps_dir)):
    d = os.path.join(maps_dir, mid)
    if not os.path.isdir(d):
        continue
    src = src_by_id.get(mid)
    if src is None:
        print("no source for", mid); continue
    chk, gaps = pm.read_chk(os.path.join(pm.ROOT, src))
    g, sec = pm.parse_chk(chk, gaps)
    off, _ = sec[b"DIM "]; w, h = g.u16(off), g.u16(off + 2)
    eoff, _ = sec[b"ERA "]; ts = pm.load_tileset(pm.TILESETS[g.byte(eoff)])
    moff, _ = sec[b"MTXM"]
    mtwm = [g.u16(moff + i * 2) for i in range(w * h)]
    elev = pm._elev_bitmap(w, h, mtwm, ts)
    with open(os.path.join(d, "elev.bin"), "wb") as fp:
        fp.write(elev.tobytes())
    lv = [int((elev == k).sum()) for k in (0, 1, 2)]
    print("%-16s lv=%s" % (mid, lv))
    ok += 1
print("rewrote %d elev.bin" % ok)

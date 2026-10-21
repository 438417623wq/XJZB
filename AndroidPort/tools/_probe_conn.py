import sys, json, os
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm
import numpy as np

for mid, src in [("divide", r"maps\(2)The Small Divide.scm"),
                 ("bloodbath", r"maps\(4)Blood Bath.scm")]:
    r = pm.read_chk(os.path.join(pm.ROOT, src))
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    off, _ = sec[b"DIM "]
    w, h = g.u16(off), g.u16(off+2)
    off, _ = sec[b"ERA "]
    ts = pm.load_tileset(pm.TILESETS.get(g.byte(off), "platform"))
    moff, _ = sec[b"MTXM"]
    mtwm = [g.u16(moff + i*2) for i in range(w*h)]
    walk = pm._walk_bitmap(w, h, mtwm, ts)
    raw = []
    off, size = sec[b"UNIT"]
    for i in range(size//36):
        b = off + i*36
        if g.u16(b+8) == pm.START_ID:
            raw.append([g.u16(b+4), g.u16(b+6)])
    mini = pm._starts_of(g, sec)
    print("== %s  dim=%dx%d  walk.shape=%s" % (mid, w, h, walk.shape))
    print("   build_map starts (raw) :", raw)
    print("   _starts_of (mini)      :", mini)
    print("   connectivity(raw)  =", pm.connectivity(walk, raw)[0])
    print("   connectivity(mini) =", pm.connectivity(walk, mini)[0])
    print("   census connected   =", pm.map_census(src)["connected"])

"""Elevation + ramp census: is divide a plateau map whose ramps were lost?

Reads the jungle tileset's VF4 straight out of the CHK's tileset (via
pipeline_maps) and reports, per map:
  - the low/mid/high ground census of the walkable bitmap
  - how many walkable cells of DIFFERENT level touch (those are the transitions
    a unit can actually use: ramps, or level changes that need no ramp)
  - the ramp bit (VF4 bit 4) count
A melee map whose two starts sit on different levels with zero such transitions
has lost its ramps; one with plenty of transitions is simply walled off.
"""
import os, sys, collections
import numpy as np

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"

CACHE = {}


def ts_for(src, era):
    key = (src, era)
    if key not in CACHE:
        CACHE[key] = pm.load_tileset(era)
    return CACHE[key]


def analyze(name, src, era):
    g = pm.read_chk(src)
    ts = ts_for(src, era)
    w, h = g["w"], g["h"]
    walk = pm._walk_bitmap(w, h, g["mtxm"], ts)
    elev = pm._elev_bitmap(w, h, g["mtxm"], ts)
    # ramp bit straight from VF4
    m = np.asarray(g["mtxm"], dtype=np.uint32).reshape(h, w)
    grp = np.clip((m & 0x7FF0) >> 4, 0, len(ts["cv5_tiles"]) - 1)
    var = m & 0xF
    vx4m = np.asarray(ts["cv5_tiles"], dtype=np.int64)[grp, var]
    n_ref = len(ts["vx4_refs"])
    vx4m = np.where(vx4m >= n_ref, 0, vx4m)
    flags = np.asarray(ts["vf4_flags"], dtype=np.int64)
    f = flags[np.clip(vx4m, 0, len(flags) - 1)]
    f = f.reshape(h, w, 4, 4).transpose(0, 2, 1, 3).reshape(h * 4, w * 4)
    ramp = ((f & 16) != 0)
    walkb = walk != 0

    census = collections.Counter()
    for lv in (0, 1, 2):
        census[lv] = int(((elev == lv) & walkb).sum())
    blocked = int((~walkb).sum())

    # walkable cells of different level that touch (4-neighbour)
    trans = 0
    for dy, dx in ((0, 1), (1, 0)):
        a = walkb[: elev.shape[0] - dy, : elev.shape[1] - dx]
        b = walkb[dy:, dx:]
        ea = elev[: elev.shape[0] - dy, : elev.shape[1] - dx]
        eb = elev[dy:, dx:]
        trans += int((a & b & (ea != eb)).sum())
    return dict(name=name, w=w, h=h, walkable=int(walkb.sum()), blocked=blocked,
                ramp=int(ramp.sum()), census=dict(census), trans=trans,
                eras=era)


rows = []
for src, mid, _n, era in pm.MAPS:
    try:
        rows.append(analyze(mid, src, era))
    except Exception as e:
        rows.append(dict(name=mid, err=str(e)[:70]))

print("%-18s %4s %4s %8s %8s %6s %18s %8s" % (
    "map", "w", "h", "walkable", "blocked", "ramp", "walkable low/mid/high", "levelTouches"))
for r in rows:
    if "err" in r:
        print("%-18s  ERR %s" % (r["name"], r["err"]))
        continue
    c = r["census"]
    print("%-18s %4d %4d %8d %8d %6d  %6d/%-6d/%-5d %8d" % (
        r["name"], r["w"], r["h"], r["walkable"], r["blocked"], r["ramp"],
        c.get(0, 0), c.get(1, 0), c.get(2, 0), r["trans"]))

jungle = [r for r in rows if "err" not in r and r["name"] in (
    "divide", "nightfall", "ashrigo", "riverruns", "plainsofsnow", "frozensea",
    "junglerumble", "killingfields", "darkcrystal", "cyclone", "closeencounters")]
print()
print("jungle-tileset maps with ramp>0:", [r["name"] for r in jungle if r["ramp"] > 0])
print("any map with ramp>0:", sorted(r["name"] for r in rows if "err" not in r and r["ramp"] > 0))

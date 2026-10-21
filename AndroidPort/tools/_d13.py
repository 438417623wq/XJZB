"""Batch D probe 13: is divide genuinely cliff-divided, or is a ramp decode
wrong? (a) global VF4 flag census per tileset, (b) per-map flag census for all
nine maps, (c) count ramp-flagged (0x10) minitiles the map actually uses.
"""
import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm

ASSETS = os.path.join(pm.ROOT, r"AndroidPort\app\app\src\main\assets\maps")
SRC = {}


def src_for(mid):
    for s, m, _n in pm.MAPS:
        if m == mid:
            return s
    return None


print("--- global VF4 census (all minitiles in the file)")
for ts in ("badlands", "platform", "install", "ashworld", "jungle",
           "desert", "ice", "twilight"):
    T = pm.load_tileset(ts)
    if not T:
        continue
    c = collections.Counter()
    for row in T["vf4_flags"]:
        for fl in row:
            c[fl] += 1
    tot = sum(c.values())
    ramp = sum(n for fl, n in c.items() if fl & 0x10)
    walk = sum(n for fl, n in c.items() if fl & 1)
    print("   %-9s minitiles=%-7d walkable=%-7d ramp=%-6d distinct=%d" % (
        ts, tot, walk, ramp, len(c)))

print()
print("--- per-map VF4 flag census")
for mid in sorted(os.listdir(ASSETS)):
    d = os.path.join(ASSETS, mid)
    if not os.path.isdir(d):
        continue
    meta = pm.json.load(open(os.path.join(d, "meta.json"), encoding="utf8"))
    s = src_for(mid)
    if not s:
        continue
    w, h = meta["w"], meta["h"]
    chk, gaps = pm.read_chk(os.path.join(pm.ROOT, s))
    g, sec = pm.parse_chk(chk, gaps)
    mo, _ = sec[b"MTXM"]
    T = pm.load_tileset(meta["tileset"])
    c = collections.Counter()
    for i in range(w * h):
        v = g.u16(mo + i * 2)
        grp = (v & 0x7FF0) >> 4
        var = v & 0xF
        vx4m = T["cv5_tiles"][grp][var] if grp < len(T["cv5_tiles"]) else 0
        if vx4m < len(T["vf4_flags"]):
            for fl in T["vf4_flags"][vx4m]:
                c[fl] += 1
    ramp = sum(n for fl, n in c.items() if fl & 0x10)
    print("   %-12s %-9s flags=%s  ramp-minitiles=%d" % (
        mid, meta["tileset"],
        " ".join("0x%04X:%d" % (fl, n) for fl, n in c.most_common(6)), ramp))

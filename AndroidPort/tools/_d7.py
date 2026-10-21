"""Batch D probe 7: why are platform CV5 groups 2/3 all-zero tiles?

Checks (a) whether BrooDat also carries platform.cv5 and whether it differs,
(b) whether a .vx4ex exists, (c) what TILE says at the black tiles, (d) what
VR4[0] / palette[0] are, (e) whether the black tiles are walkable.
"""
import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from gapio import GapReader

TILESET = {0: "badlands", 1: "platform", 2: "install", 3: "ashworld",
           4: "jungle", 5: "desert", 6: "ice", 7: "twilight"}

print("--- archive membership for platform tileset files")
for ext in ("cv5", "vx4", "vx4ex", "vr4", "vf4", "wpe"):
    p = "tileset\\platform.%s" % ext
    print("   %-8s SD=%s BD=%s" % (ext, pm.SD.has(p), pm.BD.has(p)))

for ar, nm in ((pm.SD, "StarDat"), (pm.BD, "BrooDat")):
    p = "tileset\\platform.cv5"
    if ar.has(p):
        d, g = ar.read_with_gaps(p)
        full = len(d) + sum(s for _, s in (g or []))
        print("   %s platform.cv5 short=%d full=%d groups=%d gaps=%s" % (
            nm, len(d), full, full // 52, g))

print("--- other tileset file lists")
for ts in ("badlands", "install", "ashworld", "jungle"):
    names = [n for n in ("cv5", "vx4", "vx4ex", "vr4", "vf4")
             if pm.SD.has("tileset\\%s.%s" % (ts, n)) or pm.BD.has("tileset\\%s.%s" % (ts, n))]
    print("   %-9s %s" % (ts, names))

print("--- bloodbath TILE vs MTXM at black tiles")
chk, gaps = pm.read_chk(os.path.join(pm.ROOT, r"maps\(4)Blood Bath.scm"))
g, sec = pm.parse_chk(chk, gaps)
o, _ = sec[b"DIM "]
w, h = g.u16(o), g.u16(o + 2)
eo, _ = sec[b"ERA "]
ts = TILESET.get(g.byte(eo), "platform")
d, gg = pm.SD.read_with_gaps("tileset\\platform.cv5")
cv = GapReader(d, gg or [])
n = (len(d) + sum(s for _, s in (gg or []))) // 52
cv5tiles = [[cv.u16(m * 52 + 20 + k * 2) for k in range(16)] for m in range(n)]
mo, _ = sec[b"MTXM"]
mv = [g.u16(mo + i * 2) for i in range(w * h)]
tv = None
if b"TILE" in sec:
    to, _ = sec[b"TILE"]
    tv = [g.u16(to + i * 2) for i in range(w * h)]
print("   TILE present=%s" % (tv is not None))
diff = 0
for i in range(w * h):
    mg = (mv[i] & 0x7FF0) >> 4
    if mg in (2, 3):
        if tv is not None:
            tg = (tv[i] & 0x7FF0) >> 4
            if tg != mg:
                diff += 1
                if diff < 6:
                    print("   tile %d (%d,%d) MTXM grp %d -> TILE grp %d (raw 0x%04X)" % (
                        i, i % w, i // w, mg, tg, tv[i]))
print("   black tiles=%d  TILE differs at %d of them" % (
    sum(1 for v in mv if ((v & 0x7FF0) >> 4) in (2, 3)), diff))

print("--- VR4[0] and palette[0]")
T = pm.load_tileset("platform")
print("   vr4[0] =", list(T["pixels"][0]))
print("   pal[0] =", T["pal"][0], " pal[1] =", T["pal"][1])
print("   vx4_refs[0] =", T["vx4_refs"][0])
print("--- walkability of black tiles")
print("   vf4 for vr4 idx used by megatile 0 ->", T["walkable"][0])

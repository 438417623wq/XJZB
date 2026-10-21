"""v2.44: does divide's MTXM reference megatiles that our VX4 table does not have?

pipeline_maps._walk_bitmap does:
    vx4m = tiles[grp, var]
    vx4m = np.where(vx4m >= n_ref, 0, vx4m)      # out of range -> megatile 0
and megatile 0's VF4 flags are then used for those tiles. If the gap-restored
VX4 table is short, a whole class of tiles silently inherits megatile 0's
walkability -- which would draw a fake barrier across the map.

This counts, for divide, how many tiles hit that clamp and what their art/flags
look like.
"""
import os
import sys

import numpy as np

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

SCM = os.path.join(pm.ROOT, r"maps\(2)The Small Divide.scm")
res = pm.read_chk(SCM)
chk, gaps = res
g, sec = pm.parse_chk(chk, gaps)

off, _ = sec[b"DIM "]
w = g.u16(off)
h = g.u16(off + 2)
print("DIM %dx%d" % (w, h))

eoff, _ = sec[b"ERA "]
era = g.byte(eoff)
ts = pm.load_tileset(pm.TILESETS.get(era, "platform"))
print("ERA %d -> tileset %s" % (era, ts["name"]))
print("n_vx4_refs=%d n_vf4_flags=%d n_cv5=%d"
      % (len(ts["vx4_refs"]), len(ts["vf4_flags"]), len(ts["cv5_tiles"])))

moff, _ = sec[b"MTXM"]
mt = np.array([g.u16(moff + 2 * i) for i in range(w * h)], dtype=np.uint32).reshape(h, w)
grp = (mt & 0x7FF0) >> 4
var = mt & 0xF
tiles = np.asarray(ts["cv5_tiles"], dtype=np.int64)
print("cv5 groups=%d ; MTXM grp min=%d max=%d" % (tiles.shape[0], grp.min(), grp.max()))

grpc = np.clip(grp, 0, tiles.shape[0] - 1)
clamped_grp = int((grp != grpc).sum())
vx4m = tiles[grpc, var]
n_ref = len(ts["vx4_refs"])
oob = vx4m >= n_ref
print("tiles with grp clamped: %d" % clamped_grp)
print("tiles whose vx4 ref >= n_ref: %d  (%.2f%% of %d)"
      % (int(oob.sum()), 100.0 * oob.sum() / (w * h), w * h))

if oob.any():
    vals = np.unique(vx4m[oob])
    print("  offending ref values (first 20): %s" % vals[:20])
    ys, xs = np.where(oob)
    print("  bbox of offending tiles: x %d..%d y %d..%d" % (xs.min(), xs.max(), ys.min(), ys.max()))
    print("  offending minitiles: %d of %d" % (int(oob.sum()) * 16, w * h * 16))

# What do the clamped tiles look like on the walk bitmap?  Compare against a
# build where out-of-range refs are treated as walkable instead.
walk_asis = pm._walk_bitmap(w, h, mt, ts)
flags = np.asarray(ts["vf4_flags"], dtype=np.int64)
valid = vx4m < len(flags)
f_safe = flags[np.clip(vx4m, 0, len(flags) - 1)]
f_alt = np.where(valid[..., None], f_safe, 0x0001)      # unknown -> walkable
f_alt = f_alt.reshape(h, w, 4, 4)
walk_alt = (f_alt & 1).astype(np.uint8).transpose(0, 2, 1, 3).reshape(h * 4, w * 4)

print()
print("walkable minitiles: as-is=%d  unknown-treated-walkable=%d"
      % (int(walk_asis.sum()), int(walk_alt.sum())))


def comps_of(walk):
    MW, MH = walk.shape[1], walk.shape[0]
    comp = -np.ones((MH, MW), dtype=np.int32)
    cid = 0
    for sy in range(MH):
        for sx in range(MW):
            if comp[sy, sx] != -1 or not walk[sy, sx]:
                continue
            stack = [(sx, sy)]
            comp[sy, sx] = cid
            while stack:
                x, y = stack.pop()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < MW and 0 <= ny < MH and walk[ny, nx] and comp[ny, nx] == -1:
                            comp[ny, nx] = cid
                            stack.append((nx, ny))
            cid += 1
    return comp, cid


for label, walk in (("as-is", walk_asis), ("alt", walk_alt)):
    comp, n = comps_of(walk)
    a = comp[240 // 8, 320 // 8]
    b = comp[1776 // 8, 1728 // 8]
    sizes = np.bincount(comp[comp >= 0].ravel())
    print("%-6s comps=%-4d player=%d enemy=%d SAME=%s" % (label, n, a, b, a == b))

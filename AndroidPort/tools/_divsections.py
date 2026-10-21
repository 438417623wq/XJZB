"""v2.44: three things that could still explain divide's split.

1. Section sizes.  If MTXM holds more than w*h u16 the DIM field is lying and we
   only baked the top-left corner of the real map.
2. Where divide's resources actually are, per component -- a zerg base needs a
   patch next to it, so the relocation target must be scored by mineral distance,
   not by distance from the player.
3. The resource IDs, so the component scan uses the same rule the bake does.
"""
import os
import sys

import numpy as np

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

SCM = os.path.join(pm.ROOT, r"maps\(2)The Small Divide.scm")
chk, gaps = pm.read_chk(SCM)
g, sec = pm.parse_chk(chk, gaps)

print("== section sizes")
for key in sorted(sec):
    try:
        name = key.decode("ascii")
    except Exception:
        name = repr(key)
    off, size = sec[key]
    print("   %-6s off=%-8d size=%-8d" % (name, off, size))

off, _ = sec[b"DIM "]
w, h = g.u16(off), g.u16(off + 2)
moff, msize = sec[b"MTXM"]
print("DIM %dx%d -> expected MTXM bytes %d, actual %d, ratio %.3f"
      % (w, h, w * h * 2, msize, msize / float(w * h * 2)))
print("gaps: %s" % (gaps,))

print()
print("== resources (CHK UNIT section)")
uoff, usize = sec[b"UNIT"]
n_units = usize // 36
minerals = []
geysers = []
starts = []
for i in range(n_units):
    b = uoff + i * 36
    x = g.u16(b + 4)
    y = g.u16(b + 6)
    uid = g.u16(b + 8)
    if uid in pm.MINERAL_IDS:
        minerals.append((x, y, uid))
    elif uid == pm.GEYSER_ID:
        geysers.append((x, y))
    elif uid == pm.START_ID:
        starts.append((x, y))
print("minerals=%d geysers=%d starts=%s" % (len(minerals), len(geysers), starts))


def load_walk():
    import gzip
    p = os.path.join(pm.OUT, "maps", "divide", "walk.bin.gz")
    with open(p, "rb") as fh:
        raw = gzip.decompress(fh.read())
    return np.frombuffer(raw, dtype=np.uint8).reshape(256, 256)


walk = load_walk()
MH, MW = walk.shape
comp = -np.ones((MH, MW), dtype=np.int32)
cid = 0
for sy in range(MH):
    for sx in range(MW):
        if comp[sy, sx] != -1 or not walk[sy, sx]:
            continue
        st = [(sx, sy)]
        comp[sy, sx] = cid
        while st:
            x, y = st.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < MW and 0 <= ny < MH and walk[ny, nx] and comp[ny, nx] == -1:
                        comp[ny, nx] = cid
                        st.append((nx, ny))
        cid += 1


def snap(mx, my, maxr=40):
    for r in range(maxr + 1):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                x, y = mx + dx, my + dy
                if 0 <= x < MW and 0 <= y < MH and walk[y, x]:
                    return comp[y, x], r
    return -1, -1


print()
print("== which component each resource sits in (minitile = worldpx/8)")
for label, lst in (("mineral", [(x, y) for x, y, _ in minerals]), ("geyser", geysers)):
    per = {}
    for x, y in lst:
        c, r = snap(x // 8, y // 8)
        per.setdefault(c, []).append((x, y, r))
    for c in sorted(per):
        print("   comp%-3d %-8s n=%-3d e.g. %s" % (c, label, len(per[c]), per[c][:3]))

print()
print("== per-component resource counts")
for c in range(cid):
    ys, xs = np.where(comp == c)
    if len(xs) < 200:
        continue
    mn = sum(1 for x, y, _ in minerals if snap(x // 8, y // 8)[0] == c)
    gy = sum(1 for x, y in geysers if snap(x // 8, y // 8)[0] == c)
    print("   comp%-3d size=%-6d minerals=%-3d geysers=%-2d bbox minitile=[%d,%d,%d,%d]"
          % (c, len(xs), mn, gy, xs.min(), ys.min(), xs.max(), ys.max()))

print()
print("== the 7 blocking minitiles, with their megatile and that megatile's walk pattern")
mt = np.array([g.u16(moff + 2 * i) for i in range(w * h)], dtype=np.uint32).reshape(h, w)
eoff, _ = sec[b"ERA "]
ts = pm.load_tileset(pm.TILESETS.get(g.byte(eoff), "platform"))
tiles = np.asarray(ts["cv5_tiles"], dtype=np.int64)
fl = np.asarray(ts["vf4_flags"], dtype=np.int64)
vx4m_all = tiles[np.clip((mt & 0x7FF0) >> 4, 0, tiles.shape[0] - 1), mt & 0xF]
for (mx, my) in [(189, 14), (109, 131), (110, 130), (111, 129), (158, 106), (159, 107), (216, 164)]:
    tx, ty = mx // 4, my // 4
    tile = mt[ty, tx]
    grp = int((tile & 0x7FF0) >> 4)
    var = int(tile & 0xF)
    vx4m = int(vx4m_all[ty, tx])
    sub = int(mx % 4) + 4 * int(my % 4)
    pat = "".join("W" if (int(fl[vx4m][k]) & 1) else "." for k in range(16))
    print("   minitile(%3d,%3d) tile(%2d,%2d) grp=%-5d var=%-2d vx4m=%-5d sub=%2d  pattern=%s"
          % (mx, my, tx, ty, grp, var, vx4m, sub, pat))

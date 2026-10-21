"""Decide whether divide's 7 blocking minitiles are a real cliff or a hairline crack.

For each of the 7 cells the cheapest A->B route must cross, print:
  - the cell's own VF4 flag word and walk bit
  - all 8 neighbours: flag word + walk bit
  - how many of the 16 minitiles of the SAME megatile are walkable
  - whether the cell is part of a 1-cell-wide blocked structure
Also cross-check the CHK-derived walk bitmap against the baked walk.bin.gz.
"""
import sys, gzip, collections
import numpy as np

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

SRC = r"F:\KF\XJZB\maps\(2)The Small Divide.scm"
BAKED = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide\walk.bin.gz"

chk, gaps = pm.read_chk(SRC)
g, sec = pm.parse_chk(chk, gaps)
off, _ = sec[b"DIM "]
w, h = g.u16(off), g.u16(off + 2)
off, _ = sec[b"ERA "]
era = g.byte(off)
ts = pm.load_tileset(pm.TILESETS.get(era, "platform"))
off, size = sec[b"MTXM"]
mtwm = [g.u16(off + i * 2) for i in range(w * h)]

m = np.asarray(mtwm, dtype=np.uint32).reshape(h, w)
grp = (m & 0x7FF0) >> 4
var = m & 0xF
cv5 = np.asarray(ts["cv5_tiles"], dtype=np.int64)
n_ref = len(ts["vx4_refs"])
vx4m = cv5[np.clip(grp, 0, len(cv5) - 1), var]
vx4m = np.where(vx4m >= n_ref, 0, vx4m)
fl = np.asarray(ts["vf4_flags"], dtype=np.int64)
valid = vx4m < len(fl)
fw = np.where(valid[..., None], fl[np.clip(vx4m, 0, len(fl) - 1)], 0)
fw = fw.reshape(h, w, 4, 4).transpose(0, 2, 1, 3).reshape(h * 4, w * 4)
walk = ((fw & 1) != 0)
print("tileset=%s era=%d  map=%dx%d tiles  minitiles=%dx%d" % (
    pm.TILESETS.get(era, "?"), era, w, h, w * 4, h * 4))
print("n_flag=%d n_refs=%d len(vf4_flags)=%d" % (len(fl), n_ref, len(fl)))

# --- cross-check against the baked runtime bitmap -------------------------
with gzip.open(BAKED, "rb") as f:
    baked = np.frombuffer(f.read(), dtype=np.uint8).reshape(h * 4, w * 4)
bakedw = baked != 0
diff = int((bakedw != walk).sum())
print("baked vs CHK walk bitmap: differing minitiles = %d  (baked walkable=%d, chk walkable=%d)"
      % (diff, int(bakedw.sum()), int(walk.sum())))
if diff:
    ys, xs = np.nonzero(bakedw != walk)
    print("  first 20 differences (x,y,baked,chk):")
    for i in range(min(20, len(ys))):
        print("    (%3d,%3d) baked=%d chk=%d fw=0x%04X"
              % (xs[i], ys[i], bakedw[ys[i], xs[i]], walk[ys[i], xs[i]], fw[ys[i], xs[i]]))

CELLS = [(189, 14), (109, 131), (110, 130), (111, 129),
         (158, 106), (159, 107), (216, 164)]

print()
print("=== per-cell neighbourhood ===")
for (x, y) in CELLS:
    print("cell minitile(%d,%d) tile(%d,%d) worldpx=(%d,%d) fw=0x%04X walk=%d"
          % (x, y, x // 4, y // 4, x * 8, y * 8, fw[y, x], walk[y, x]))
    row = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            nx, ny = x + dx, y + dy
            if nx < 0 or ny < 0 or nx >= w * 4 or ny >= h * 4:
                row.append("  out ")
                continue
            row.append("%s%04X" % ("W" if walk[ny, nx] else ".", fw[ny, nx]))
    print("   neighbours (3x3, W=walkable): " + " ".join(row[:3]))
    print("                                 " + " ".join(row[3:6]))
    print("                                 " + " ".join(row[6:9]))
    # megatile of this cell
    tx, ty = x // 4, y // 4
    mg = int(grp[ty, tx])
    vr = int(var[ty, tx])
    vx = int(vx4m[ty, tx])
    sub = fw[ty * 4:ty * 4 + 4, tx * 4:tx * 4 + 4]
    print("   megatile grp=%d var=%d vx4idx=%d  sub-flags walkable=%d/16"
          % (mg, vr, vx, int((sub & 1).sum())))
    print("   sub flags: " + " ".join("%04X" % v for v in sub.reshape(-1)))

# --- how thick is the blocked structure at each cell? --------------------
print()
print("=== local wall thickness (BFS through blocked cells only) ===")
blocked = ~walk
for (x, y) in CELLS:
    # flood the blocked component containing (x,y), bounded to a 41x41 window
    R = 20
    x0, y0 = max(0, x - R), max(0, y - R)
    x1, y1 = min(w * 4, x + R + 1), min(h * 4, y + R + 1)
    win = blocked[y0:y1, x0:x1]
    lab = np.zeros_like(win, dtype=np.int32)
    comp = 0
    sizes = []
    for yy in range(win.shape[0]):
        for xx in range(win.shape[1]):
            if win[yy, xx] and lab[yy, xx] == 0:
                comp += 1
                stack = [(xx, yy)]
                lab[yy, xx] = comp
                n = 0
                while stack:
                    cx, cy = stack.pop()
                    n += 1
                    for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx2, ny2 = cx + ddx, cy + ddy
                        if 0 <= nx2 < win.shape[1] and 0 <= ny2 < win.shape[0] \
                                and win[ny2, nx2] and lab[ny2, nx2] == 0:
                            lab[ny2, nx2] = comp
                            stack.append((nx2, ny2))
                sizes.append(n)
    mine = lab[y - y0, x - x0]
    # if the window edge is blocked, the component is clipped -> report >=
    clipped = bool(win[0].any() or win[-1].any() or win[:, 0].any() or win[:, -1].any())
    print("cell(%3d,%3d): blocked component size in +/-%d window = %d%s"
          % (x, y, R, sizes[mine - 1], "  (clipped by window: real size larger)" if clipped else ""))

# --- is there any place where the two lands are separated by 1 cell only? -
print()
print("=== thinnest walkable-gap analysis on the whole map ===")
from collections import deque
lab = np.zeros((h * 4, w * 4), dtype=np.int32)
comp = 0
for yy in range(h * 4):
    for xx in range(w * 4):
        if walk[yy, xx] and lab[yy, xx] == 0:
            comp += 1
            dq = deque([(xx, yy)])
            lab[yy, xx] = comp
            while dq:
                cx, cy = dq.popleft()
                for ddx in (-1, 0, 1):
                    for ddy in (-1, 0, 1):
                        nx2, ny2 = cx + ddx, cy + ddy
                        if 0 <= nx2 < w * 4 and 0 <= ny2 < h * 4 \
                                and walk[ny2, nx2] and lab[ny2, nx2] == 0:
                            lab[ny2, nx2] = comp
                            dq.append((nx2, ny2))
cnt = collections.Counter(int(v) for v in lab.reshape(-1) if v)
print("walkable components: %d" % len(cnt))
for c, n in cnt.most_common(8):
    ys, xs = np.nonzero(lab == c)
    print("  comp%-3d size=%-7d bbox x %d..%d  y %d..%d" % (c, n, xs.min(), xs.max(), ys.min(), ys.max()))

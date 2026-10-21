# v2.44: pick a home for m01's zerg base on the PLAYER's landmass.
#
# divide's raw walk bitmap splits the map into two landmasses (the cliff band
# between them is real art -- see _crossing*.py). m01's zerg base and both wave
# spawn points sit on the far one, so every wave unit's setPath() fails and the
# tutorial is a walkover. This script finds a spot on the player's component that
# fits a 4x4-tile hatchery footprint, is a long walk from the player's command
# center, and keeps the base in roughly the same compass direction it has now.
import gzip
import os
from collections import deque

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
MAP = "divide"

d = os.path.join(ASSETS, "maps", MAP)
meta = {}
for line in open(os.path.join(d, "meta.txt"), encoding="utf-8", errors="replace"):
    if "=" in line:
        k, v = line.split("=", 1)
        meta.setdefault(k.strip(), []).append(v.strip())
W_T = int(meta["w"][0])
H_T = int(meta["h"][0])
W, H = W_T * 4, H_T * 4
walk = gzip.decompress(open(os.path.join(d, "walk.bin.gz"), "rb").read())

lab = [-1] * (W * H)
n = 0
for i in range(W * H):
    if lab[i] != -1 or not walk[i]:
        continue
    lab[i] = n
    q = deque([i])
    while q:
        c = q.popleft()
        x, y = c % W, c // W
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                X, Y = x + dx, y + dy
                if 0 <= X < W and 0 <= Y < H:
                    j = Y * W + X
                    if lab[j] == -1 and walk[j]:
                        lab[j] = n
                        q.append(j)
    n += 1

PLAYER_CC = (320, 240)
pc = lab[(PLAYER_CC[1] // 8) * W + (PLAYER_CC[0] // 8)]
print("map %dx%d tiles, comps=%d, player comp=%d" % (W_T, H_T, n, pc))
sizes = {}
bbox = {}
for i, c in enumerate(lab):
    if c < 0:
        continue
    sizes[c] = sizes.get(c, 0) + 1
    x, y = i % W, i // W
    b = bbox.get(c)
    if b is None:
        bbox[c] = [x, y, x, y]
    else:
        b[0] = min(b[0], x); b[1] = min(b[1], y)
        b[2] = max(b[2], x); b[3] = max(b[3], y)
for c in sorted(sizes, key=lambda k: -sizes[k])[:6]:
    print("  comp%d size=%d bbox minitile=%s worldpx=(%d,%d)-(%d,%d)"
          % (c, sizes[c], bbox[c], bbox[c][0] * 8, bbox[c][1] * 8,
             bbox[c][2] * 8, bbox[c][3] * 8))
print("current enemy hatchery (1728,1776) comp=%d"
      % lab[(1776 // 8) * W + (1728 // 8)])


def walkable_tile(tx, ty):
    for my in range(4):
        for mx in range(4):
            X, Y = tx * 4 + mx, ty * 4 + my
            if not (0 <= X < W and 0 <= Y < H) or not walk[Y * W + X]:
                return False
    return True


def comp_of_tile(tx, ty):
    return lab[(ty * 4) * W + (tx * 4)]


def fits(tx, ty, tiles):
    half = tiles // 2
    for y in range(ty - half, ty - half + tiles):
        for x in range(tx - half, tx - half + tiles):
            if not (0 <= x < W_T and 0 <= y < H_T) or not walkable_tile(x, y):
                return False
    return True


cands = []
for ty in range(2, H_T - 2):
    for tx in range(2, W_T - 2):
        if comp_of_tile(tx, ty) != pc:
            continue
        wx, wy = tx * 32 + 16, ty * 32 + 16
        dist = ((wx - PLAYER_CC[0]) ** 2 + (wy - PLAYER_CC[1]) ** 2) ** 0.5
        cands.append((dist, wx, wy))
cands.sort(reverse=True)
print("tiles on player comp=%d, farthest dist=%.0f" % (len(cands), cands[0][0]))
for dist, wx, wy in cands[:12]:
    print("   d=%-7.0f (%d,%d) fits4=%s" % (dist, wx, wy, fits(wx // 32, wy // 32, 4)))
best = None
for dist, wx, wy in cands:
    if dist < 700:
        break
    if not fits(wx // 32, wy // 32, 4):
        continue
    score = abs(dist - 1150)
    if best is None or score < best[0]:
        best = (score, wx, wy, dist)
print("candidate hatchery:", best)

if best:
    hx, hy = best[1], best[2]
    print("hatchery  (%d,%d)" % (hx, hy))
    for key, tiles, ox, oy in (("pool", 3, -160, 70), ("sunkenA", 2, 130, 90),
                               ("sunkenB", 2, 90, 90), ("z1", 0, -80, 120),
                               ("z2", 0, -54, 120), ("z3", 0, -28, 120)):
        want = (hx + ox, hy + oy)
        spot = None
        for r in range(0, 200, 8):
            for dy in range(-r, r + 1, 8):
                for dx in range(-r, r + 1, 8):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    cx, cy = want[0] + dx, want[1] + dy
                    tx, ty = cx // 32, cy // 32
                    if not (0 <= tx < W_T and 0 <= ty < H_T):
                        continue
                    if comp_of_tile(tx, ty) != pc:
                        continue
                    if tiles and not fits(tx, ty, tiles):
                        continue
                    if not tiles and not walkable_tile(tx, ty):
                        continue
                    spot = (tx * 32 + 16, ty * 32 + 16)
                    break
                if spot:
                    break
            if spot:
                break
        print("%-8s want(%d,%d) -> %s" % (key, want[0], want[1], spot))

# wave spawn: a walkable spot on the player's landmass, away from the base,
# roughly where the current ones are but pulled toward the player's side
for want in ((1500, 1500), (1450, 1450)):
    spot = None
    for r in range(0, 900, 16):
        for dy in range(-r, r + 1, 16):
            for dx in range(-r, r + 1, 16):
                if max(abs(dx), abs(dy)) != r:
                    continue
                cx, cy = want[0] + dx, want[1] + dy
                tx, ty = cx // 32, cy // 32
                if not (0 <= tx < W_T and 0 <= ty < H_T):
                    continue
                if comp_of_tile(tx, ty) != pc or not walkable_tile(tx, ty):
                    continue
                dcc = ((cx - PLAYER_CC[0]) ** 2 + (cy - PLAYER_CC[1]) ** 2) ** 0.5
                if dcc < 900:
                    continue
                spot = (cx, cy)
                break
            if spot:
                break
        if spot:
            break
    print("wave from want(%d,%d) -> %s" % (want[0], want[1], spot))

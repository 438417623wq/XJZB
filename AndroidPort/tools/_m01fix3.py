"""v2.44: build a full m01 layout on divide's player component.

divide is the one baked map whose two start landmasses are not connected (see
_missionconn.py), so m01's enemy base and every scripted wave spawn sat on a
landmass the zerg can never leave: the waves called setPath, findPath failed,
and the units stood still. This script re-derives the components from the
runtime walk.bin.gz, picks an enemy base cluster inside the PLAYER's component,
picks two wave spawn points there too, and verifies with A* that the enemy can
actually march to the player.
"""
import gzip
import heapq
import os

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"

with open(os.path.join(ASSETS, "maps", "divide", "meta.txt"), "r", encoding="utf-8", errors="replace") as f:
    meta = f.read()
W = H = 0
for line in meta.splitlines():
    if line.startswith("w="):
        W = int(line[2:])
    elif line.startswith("h="):
        H = int(line[2:])

with gzip.open(os.path.join(ASSETS, "maps", "divide", "walk.bin.gz"), "rb") as f:
    raw = f.read()
MW, MH = W * 4, H * 4
walk = [b != 0 for b in raw]


def wm(mx, my):
    return 0 <= mx < MW and 0 <= my < MH and walk[my * MW + mx]


def tile_ok(tx, ty):
    return all(wm(tx * 4 + dx, ty * 4 + dy) for dy in range(4) for dx in range(4))


# ---- components -------------------------------------------------------------
comp = [-1] * (MW * MH)
comps = []
for start in range(MW * MH):
    if comp[start] != -1 or not walk[start]:
        continue
    cid = len(comps)
    stack = [start]
    comp[start] = cid
    size = 0
    while stack:
        i = stack.pop()
        size += 1
        x, y = i % MW, i // MW
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < MW and 0 <= ny < MH:
                    j = ny * MW + nx
                    if walk[j] and comp[j] == -1:
                        comp[j] = cid
                        stack.append(j)
    comps.append(size)

PLAYER = (320, 240)
pcomp = comp[(PLAYER[1] // 8) * MW + (PLAYER[0] // 8)]
print("divide %dx%d tiles; player CC %s -> comp%d size=%d" % (W, H, PLAYER, pcomp, comps[pcomp]))


def in_pcomp(wx, wy, tiles):
    tx0, ty0 = int(wx) // 32 - tiles // 2, int(wy) // 32 - tiles // 2
    for ty in range(ty0, ty0 + max(tiles, 1)):
        for tx in range(tx0, tx0 + max(tiles, 1)):
            if not (0 <= tx < W and 0 <= ty < H):
                return False
            if comp[(ty * 4) * MW + tx * 4] != pcomp:
                return False
    return True


def footprint_ok(wx, wy, tiles):
    tx0, ty0 = int(wx) // 32 - tiles // 2, int(wy) // 32 - tiles // 2
    for ty in range(ty0, ty0 + max(tiles, 1)):
        for tx in range(tx0, tx0 + max(tiles, 1)):
            if not (0 <= tx < W and 0 <= ty < H) or not tile_ok(tx, ty):
                return False
    return True


def ok(wx, wy, tiles):
    return footprint_ok(wx, wy, tiles) and in_pcomp(wx, wy, tiles)


def snap(wx, wy, tiles, maxr=40):
    """Nearest spot legal for `tiles` AND inside the player's component."""
    if ok(wx, wy, tiles):
        return int(wx), int(wy)
    for r in range(1, maxr + 1):
        for dx in range(-r, r + 1):
            for dy in (-r, r):
                for (x, y) in ((wx + dx * 32, wy + dy * 32), (wx + dy * 32, wy + dx * 32)):
                    if ok(x, y, tiles):
                        return int(x), int(y)
    return None


def dist_to_player(wx, wy):
    return ((wx - PLAYER[0]) ** 2 + (wy - PLAYER[1]) ** 2) ** 0.5


# ---- enemy base cluster -----------------------------------------------------
# The hatchery wants the far corner of the player's landmass: far enough to give
# the player time, close enough that the AI can actually march.
sites = []
for ty in range(2, H - 2):
    for tx in range(2, W - 2):
        wx, wy = tx * 32 + 16, ty * 32 + 16
        if ok(wx, wy, 4):
            sites.append((dist_to_player(wx, wy), wx, wy))
sites.sort(reverse=True)
print("legal 4x4 sites in comp%d: %d; farthest: %s" % (pcomp, len(sites), sites[0][1:]))

# Keep a clear lane: prefer a site 900..1300px out so waves have room to march.
HATCH = None
for d, wx, wy in sites:
    if 900 <= d <= 1300:
        HATCH = (wx, wy)
        break
if HATCH is None:
    HATCH = (sites[0][1], sites[0][2])
print("hatchery -> %s dist=%.0f" % (HATCH, dist_to_player(*HATCH)))


def place(want, tiles, label):
    got = snap(*want, tiles)
    assert got is not None, label + ": no legal spot"
    print("  %-9s want%s -> %s" % (label, want, got))
    return got


pool = place((HATCH[0] - 160, HATCH[1] + 64), 3, "pool")
sunken_a = place((HATCH[0] + 96, HATCH[1] + 96), 2, "sunkenA")
sunken_b = place((HATCH[0] + 64, HATCH[1] + 128), 2, "sunkenB")
z1 = place((HATCH[0] - 96, HATCH[1] + 112), 0, "z1")
z2 = place((HATCH[0] - 64, HATCH[1] + 112), 0, "z2")
z3 = place((HATCH[0] - 32, HATCH[1] + 112), 0, "z3")

# ---- wave spawn points ------------------------------------------------------
# On the player's component, between the enemy base and the player, so the wave
# reads as "they marched in" rather than "they popped out of thin air".
for want in ((1450, 1450), (1500, 1500)):
    got = snap(*want, 0, maxr=80)
    print("wave from want%s -> %s dist=%.0f" % (want, got, dist_to_player(*got) if got else -1))

# ---- A* sanity --------------------------------------------------------------
DX = (1, -1, 0, 0, 1, 1, -1, -1)
DY = (0, 0, 1, -1, 1, -1, 1, -1)
WEIGHT, TIE = 2.0, 0.1


def astar(sx, sy, gx, gy, cap=200000):
    n = MW * MH
    g = [0.0] * n
    seen = [False] * n
    s, goal = sy * MW + sx, gy * MW + gx
    h0 = (abs(sx - gx) + abs(sy - gy)) + (1.4142 - 2) * min(abs(sx - gx), abs(sy - gy))
    heap = [(WEIGHT * h0, 0.0, s)]
    seen[s] = True
    exp = 0
    while heap and exp < cap:
        f, cost, cur = heapq.heappop(heap)
        exp += 1
        if cur == goal:
            return exp, True, cost
        cx, cy = cur % MW, cur // MW
        for d in range(8):
            nx, ny = cx + DX[d], cy + DY[d]
            if not wm(nx, ny):
                continue
            if d >= 4 and (not wm(cx + DX[d], cy) or not wm(cx, cy + DY[d])):
                continue
            ni = ny * MW + nx
            step = 1.4142 if d >= 4 else 1.0
            ng = cost + step
            if not seen[ni] or ng < g[ni] - 1e-6:
                seen[ni] = True
                g[ni] = ng
                h = (abs(nx - gx) + abs(ny - gy)) + (1.4142 - 2) * min(abs(nx - gx), abs(ny - gy))
                heapq.heappush(heap, (ng + WEIGHT * h - TIE * ng, ng, ni))
    return exp, False, -1.0


print()
for label, (wx, wy) in (("hatchery", HATCH), ("pool", pool), ("sunkenA", sunken_a), ("sunkenB", sunken_b)):
    e, found, cost = astar(wx // 8, wy // 8, PLAYER[0] // 8, PLAYER[1] // 8)
    print("A* %-9s -> player CC  expansions=%-7d found=%-5s pathLen=%.0fpx" % (label, e, found, cost * 8))

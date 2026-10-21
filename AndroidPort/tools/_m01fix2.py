"""v2.44: pick a workable m01 layout on divide.

divide is the one baked map whose two start landmasses are not connected (see
_missionconn.py), so m01's enemy base and every scripted wave spawn sat on a
landmass the zerg can never leave. This script re-derives the components from
the runtime walk.bin.gz and searches the PLAYER's component for a place to put
the enemy base, then emits the coordinates to paste into m01.json.

Footprint rule mirrors Game.occupyFootprint: for a building of `tiles` x
`tiles`, the covered tiles are tx0 .. tx0+tiles-1 with tx0 = x/32 - tiles/2,
and every one of the 16 minitiles in each covered tile must be walkable.
"""
import gzip
import os

TOOLS = r"F:\KF\XJZB\AndroidPort\tools"
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
assert len(raw) == MW * MH, (len(raw), MW * MH)
walk = [b != 0 for b in raw]


def walk_mini(mx, my):
    if mx < 0 or my < 0 or mx >= MW or my >= MH:
        return False
    return walk[my * MW + mx]


def tile_ok(tx, ty):
    """All 16 minitiles of tile (tx,ty) walkable."""
    for dy in range(4):
        for dx in range(4):
            if not walk_mini(tx * 4 + dx, ty * 4 + dy):
                return False
    return True


def footprint_ok(wx, wy, tiles):
    tx0 = int(wx) // 32 - tiles // 2
    ty0 = int(wy) // 32 - tiles // 2
    for ty in range(ty0, ty0 + tiles):
        for tx in range(tx0, tx0 + tiles):
            if tx < 0 or ty < 0 or tx >= W or ty >= H:
                return False
            if not tile_ok(tx, ty):
                return False
    return True


# ---- components (8-connected) ------------------------------------------------
comp = [-1] * (MW * MH)
comps = []
for start in range(MW * MH):
    if comp[start] != -1 or not walk[start]:
        continue
    cid = len(comps)
    stack = [start]
    comp[start] = cid
    size = 0
    minx, miny, maxx, maxy = MW, MH, -1, -1
    while stack:
        i = stack.pop()
        size += 1
        x, y = i % MW, i // MW
        if x < minx: minx = x
        if y < miny: miny = y
        if x > maxx: maxx = x
        if y > maxy: maxy = y
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= MW or ny >= MH:
                    continue
                j = ny * MW + nx
                if walk[j] and comp[j] == -1:
                    comp[j] = cid
                    stack.append(j)
    comps.append((size, minx, miny, maxx, maxy))

print("divide %dx%d tiles, %dx%d minitiles, %d walkable components" % (W, H, MW, MH, len(comps)))
for i, (size, minx, miny, maxx, maxy) in enumerate(comps):
    if size > 1000:
        print("  comp%d size=%-6d bbox minitile=[%d,%d,%d,%d] worldpx=(%d,%d)-(%d,%d)"
              % (i, size, minx, miny, maxx, maxy, minx * 8, miny * 8, maxx * 8 + 8, maxy * 8 + 8))

PLAYER = (320, 240)
pcomp = comp[(PLAYER[1] // 8) * MW + (PLAYER[0] // 8)]
print("player CC %s -> comp%d (size %d)" % (PLAYER, pcomp, comps[pcomp][0]))


def nearest_comp(wx, wy, maxr=40):
    mx, my = int(wx) // 8, int(wy) // 8
    if walk_mini(mx, my):
        return comp[my * MW + mx], 0
    for r in range(1, maxr + 1):
        for dx in range(-r, r + 1):
            for dy in (-r, r):
                for (x, y) in ((mx + dx, my + dy), (mx + dy, my + dx)):
                    if walk_mini(x, y):
                        return comp[y * MW + x], r
    return None, None


def dist_to_player(wx, wy):
    dx, dy = wx - PLAYER[0], wy - PLAYER[1]
    return (dx * dx + dy * dy) ** 0.5


# ---- candidate enemy base sites in the player's component --------------------
print()
print("== 4x4 sites in player component, sorted by distance from CC (top 20)")
cands = []
for ty in range(2, H - 2):
    for tx in range(2, W - 2):
        if not tile_ok(tx, ty):
            continue
        if comp[ty * 4 * MW + tx * 4] != pcomp:
            continue
        wx, wy = tx * 32 + 16, ty * 32 + 16
        # footprint must stay in the component too
        if not footprint_ok(wx, wy, 4):
            continue
        cands.append((dist_to_player(wx, wy), wx, wy))
cands.sort(reverse=True)
for d, wx, wy in cands[:20]:
    print("   (%4d,%4d)  dist=%.1f" % (wx, wy, d))
print("   total 4x4 sites in comp%d: %d" % (pcomp, len(cands)))

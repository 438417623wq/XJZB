"""v2.44: pick a whole zerg base site inside the PLAYER's walk component of divide.

_m01fix3.py found (1424,80) for the hatchery but placed a sunken inside the
hatchery footprint -- its ok() only asked "is the terrain walkable", never
"does this overlap something already placed".  This does the full job: for every
legal 4x4 hatchery tile, try to fit pool + 2 sunkens + 3 zerglings around it with
real footprint exclusion, and score by distance from the player CC.
"""
import gzip
import os
import sys

import numpy as np

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
MD = os.path.join(ASSETS, "maps", "divide")
TS = 32
FOOT = {"hatchery": 4, "pool": 3, "sunken": 2}
RING = [  # (label, dx, dy) in tiles relative to the hatchery centre
    ("pool", -4, 1), ("pool", 4, 2), ("pool", 1, 4), ("pool", -3, -4),
    ("sunken", -3, 0), ("sunken", 3, 0), ("sunken", 0, 3), ("sunken", 0, -3),
    ("sunken", -4, 3), ("sunken", 4, -3),
]


def load_walk():
    for name in ("walk.bin.gz", "walk.gz", "walk.bin"):
        p = os.path.join(MD, name)
        if not os.path.exists(p):
            continue
        with open(p, "rb") as fh:
            raw = fh.read()
        if name.endswith(".gz"):
            raw = gzip.decompress(raw)
        return np.frombuffer(raw, dtype=np.uint8).reshape(256, 256)
    raise SystemExit("no walk bitmap")


def main():
    walk = load_walk()
    MW = MH = 256

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
    print("components=%d" % cid)
    for c in range(cid):
        ys, xs = np.where(comp == c)
        print("  comp%d size=%-6d bbox minitile=[%d,%d,%d,%d]"
              % (c, len(xs), xs.min(), ys.min(), xs.max(), ys.max()))

    px, py = 320 // 8, 240 // 8
    pc = comp[py, px]
    print("player CC minitile=(%d,%d) comp=%d" % (px, py, pc))

    def tiles_ok(tx, ty, tiles):
        """True when the tiles x tiles tile block is fully walkable."""
        if tx < 0 or ty < 0 or tx + tiles > 64 or ty + tiles > 64:
            return False
        x0, y0 = tx * 4, ty * 4
        return bool(walk[y0:y0 + tiles * 4, x0:x0 + tiles * 4].all())

    def centre_of(tx, ty, tiles):
        """World centre the game will use for a building whose tile origin is (tx,ty)."""
        return (tx + tiles // 2) * TS + 16, (ty + tiles // 2) * TS + 16

    best = []
    for hty in range(64):
        for htx in range(64):
            if not tiles_ok(htx, hty, 4):
                continue
            # candidate centres near the hatchery, in tile space
            placed = {"hatchery": (htx, hty)}
            used = {(htx + a, hty + b) for a in range(4) for b in range(4)}
            picks = []
            for label, dx, dy in RING:
                n = FOOT[label]
                tx = htx + dx + 2 - n // 2
                ty = hty + dy + 2 - n // 2
                cells = {(tx + a, ty + b) for a in range(n) for b in range(n)}
                if cells & used:
                    continue
                if not tiles_ok(tx, ty, n):
                    continue
                used |= cells
                picks.append((label, tx, ty, n))
                if len([p for p in picks if p[0] == "pool"]) >= 1 and \
                   len([p for p in picks if p[0] == "sunken"]) >= 2:
                    break
            if len([p for p in picks if p[0] == "pool"]) < 1:
                continue
            if len([p for p in picks if p[0] == "sunken"]) < 2:
                continue
            # zerglings: any walkable minitile just outside the footprints
            zs = []
            for a in range(4):
                for b in range(4):
                    tx = htx - 1 + a
                    ty = hty + 5 + b
                    if tiles_ok(tx, ty, 1):
                        zs.append((tx * TS + 16, ty * TS + 16))
                    if len(zs) >= 3:
                        break
                if len(zs) >= 3:
                    break
            if len(zs) < 3:
                continue
            hx, hy = centre_of(htx, hty, 4)
            d = ((hx - 320) ** 2 + (hy - 240) ** 2) ** 0.5
            # every placed building must sit on the player's component
            ok = all(comp[(ty * 4 + n * 2), (tx * 4 + n * 2)] == pc for _, tx, ty, n in picks)
            ok = ok and comp[hy // 8, hx // 8] == pc
            if not ok:
                continue
            best.append((d, hx, hy, picks, zs))

    best.sort(reverse=True)
    print("candidate bases on the player's component: %d" % len(best))
    for d, hx, hy, picks, zs in best[:4]:
        print("  hatchery=(%d,%d) dist=%.1f" % (hx, hy, d))
        for label, tx, ty, n in picks:
            print("     %-8s centre=%s tiles=(%d,%d)+%d" % (label, centre_of(tx, ty, n), tx, ty, n))
        print("     zerglings=%s" % (zs,))


main()

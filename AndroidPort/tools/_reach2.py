"""v2.44: connectivity of the SHIPPED walk bitmap under the GAME's exact rule.

reachable-with-free-diagonals (and every earlier audit) overestimates: the
engine's findPath forbids cutting a diagonal corner (Game.java:3019 -- a
diagonal step needs BOTH orthogonal neighbours walkable). This script floods
with that rule, labels every component, and then asks the questions that
actually matter for gameplay on each shipped map:

  - which component does each start snap into (the game snaps with
    nearestPassMini, radius 24 -- mirrored here)?
  - do the snapped starts share one component?
  - which component does each mineral/geyser patch snap into?
  - sizes of the components involved.

Usage: python _reach2.py [map_id ...]   (default: every shipped map)
"""
import gzip
import os
import sys
from collections import deque

import numpy as np

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"


def load(mid):
    p = os.path.join(ASSETS, mid, "walk.bin.gz")
    raw = gzip.open(p, "rb").read()
    meta = {}
    for line in open(os.path.join(ASSETS, mid, "meta.txt"), encoding="utf-8"):
        line = line.strip()
        if "=" in line:
            k, v = line.split("=", 1)
            meta.setdefault(k, []).append(v)
    w = int(meta["w"][0]) * 4
    h = int(meta["h"][0]) * 4
    walk = np.frombuffer(raw, dtype=np.uint8)[: w * h].reshape(h, w).astype(bool)
    return walk, meta


def components(walk):
    """8-connected labels WITH the game's no-corner-cut rule."""
    H, W = walk.shape
    lab = np.zeros((H, W), dtype=np.int32)
    n = 0
    for sy in range(H):
        row = walk[sy]
        for sx in range(W):
            if row[sx] and lab[sy, sx] == 0:
                n += 1
                lab[sy, sx] = n
                dq = deque([(sy, sx)])
                while dq:
                    y, x = dq.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < H and 0 <= xx < W and walk[yy, xx] and lab[yy, xx] == 0:
                            lab[yy, xx] = n
                            dq.append((yy, xx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            if dy != 0 and dx != 0:
                                if not (0 <= y + dy < H and 0 <= x + dx < W
                                        and 0 <= y + dy < H and 0 <= x < W
                                        and 0 <= y < H and 0 <= x + dx < W):
                                    continue
                                # the game rule: both orthogonals must pass
                                if not (walk[y + dy, x] and walk[y, x + dx]):
                                    continue
                            yy, xx = y + dy, x + dx
                            if 0 <= yy < H and 0 <= xx < W and walk[yy, xx] and lab[yy, xx] == 0:
                                lab[yy, xx] = n
                                dq.append((yy, xx))
    return lab, n


def snap(walk, lab, x, y, max_r=24):
    """nearestPassMini mirror: nearest walkable minitile within max_r."""
    H, W = walk.shape
    best = None
    bd = 1 << 30
    for r in range(0, max_r + 1):
        for yy in range(max(0, y - r), min(H, y + r + 1)):
            for xx in range(max(0, x - r), min(W, x + r + 1)):
                if not walk[yy, xx]:
                    continue
                d = (xx - x) * (xx - x) + (yy - y) * (yy - y)
                if d < bd:
                    bd = d
                    best = (yy, xx)
        if best is not None:
            break        # same radius rings as the engine: first hit wins
    return best


def units_of(mid):
    """mineral/geyser positions in minitiles from meta.txt unit= lines."""
    out = []
    for line in open(os.path.join(ASSETS, mid, "meta.txt"), encoding="utf-8"):
        p = line.strip().split(",")
        if p and p[0] == "unit=1":
            out.append(("mineral", int(p[1]) // 8, int(p[2]) // 8))
        elif p and p[0] == "unit=2":
            out.append(("geyser", int(p[1]) // 8, int(p[2]) // 8))
    return out


def main(mids):
    for mid in mids:
        walk, meta = load(mid)
        lab, n = components(walk)
        sizes = np.bincount(lab.ravel())[1:]
        starts = []
        for s in meta.get("start", []):
            x, y = s.split(",")
            starts.append((int(x) // 8, int(y) // 8))
        seeds = [snap(walk, lab, x, y) for x, y in starts]
        comps = [int(lab[s]) if s else 0 for s in seeds]
        ok = len(set(comps)) == 1 and comps[0] != 0
        # minerals not in the start component
        far = 0
        for kind, x, y in units_of(mid):
            s = snap(walk, lab, x, y)
            if s is None:
                far += 1
                continue
            c = int(lab[s])
            if c != comps[0]:
                far += 1
        big = sorted(sizes)[-5:]
        print("%-16s comps=%-4d starts=%s compsOfStarts=%s same=%s mineralsUnreached=%d top=%s"
              % (mid, n, len(starts), comps, ok, far, big))


if __name__ == "__main__":
    ids = sys.argv[1:] or sorted(os.listdir(ASSETS))
    ids = [i for i in ids if os.path.isdir(os.path.join(ASSETS, i))]
    main(ids)

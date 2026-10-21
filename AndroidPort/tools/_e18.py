"""Batch E/D regression probe: run5 shows the player wiped (units=0) on the
regenerated terrain where run4 had 4 units. run4 ran on the OLD maps (17:53),
run5 on the NEW ones (22:27), so this checks whether the corrected walk map
leaves the player's start / spawn points walkable."""
import gzip
import os
import sys

ROOT = r"F:\KF\XJZB"
MAPS = os.path.join(ROOT, r"AndroidPort\app\app\src\main\assets\maps")


def load(map_id):
    d = os.path.join(MAPS, map_id)
    with gzip.open(os.path.join(d, "walk.bin.gz"), "rb") as f:
        walk = f.read()
    meta = {}
    starts, units = [], []
    with open(os.path.join(d, "meta.txt"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            k, _, v = line.partition("=")
            if k == "start":
                starts.append(tuple(int(x) for x in v.split(",")))
            elif k == "unit":
                units.append([int(x) for x in v.split(",")])
            else:
                meta[k] = v
    w, h = int(meta["w"]), int(meta["h"])
    return walk, w, h, starts, units


def walkable(walk, w, h, px, py):
    """walk.bin is a per-minitile byte grid at 4x tile resolution."""
    mw, mh = w * 4, h * 4
    mx, my = int(px) // 8, int(py) // 8      # 32px tile = 4 minitiles of 8px
    if not (0 <= mx < mw and 0 <= my < mh):
        return None
    return walk[my * mw + mx]


for map_id in sys.argv[1:] or ["bloodbath"]:
    walk, w, h, starts, units = load(map_id)
    print("== %s  %dx%d tiles  walk=%d bytes  expect=%d"
          % (map_id, w, h, len(walk), w * 4 * h * 4))
    for i, (sx, sy) in enumerate(starts):
        print("   start%d (%4d,%4d) walk=%s" % (i, sx, sy, walkable(walk, w, h, sx, sy)))
    from collections import Counter
    cnt = Counter()
    bad = 0
    for u in units:
        _, ux, uy, _, _, _team = u
        v = walkable(walk, w, h, ux, uy)
        cnt[v] += 1
        if v in (0, None):
            bad += 1
            if bad <= 12:
                print("   UNIT ON NON-WALKABLE (%4d,%4d) walk=%s" % (ux, uy, v))
    print("   units=%d  nonwalkable=%d  walk-value histogram=%s"
          % (len(units), bad, dict(cnt.most_common(8))))

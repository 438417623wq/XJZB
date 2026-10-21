# v2.44: which missions put their objectives on a landmass the player cannot walk to?
#
# The [v236] gate checks this with pipeline_maps' connectivity rule, which dilates
# the walk bitmap by one minitile. That dilation bridges thin cliff walls, so a
# level can pass [v236] and still be unwinnable/unattackable at runtime, where
# Game.findPath sees the raw bitmap. This script uses the RAW bitmap only -- the
# same one Game loads from walk.bin.gz -- so it measures what the game will do.
import gzip
import json
import os
import re
from collections import deque

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"


def read_walk(map_id):
    d = os.path.join(ASSETS, "maps", map_id)
    meta = {}
    for line in open(os.path.join(d, "meta.txt"), encoding="utf-8", errors="replace"):
        if "=" in line:
            k, v = line.split("=", 1)
            meta.setdefault(k.strip(), []).append(v.strip())
    w = int(meta["w"][0])
    h = int(meta["h"][0])
    raw = None
    for name in ("walk.bin.gz", "walk.gz", "walk.bin"):
        p = os.path.join(d, name)
        if os.path.exists(p):
            raw = gzip.decompress(open(p, "rb").read()) if name.endswith(".gz") \
                else open(p, "rb").read()
            break
    if raw is None:
        return w, h, None
    return w, h, bytearray(raw)


def comps(w, h, walk):
    W, H = w * 4, h * 4
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
                    if X < 0 or Y < 0 or X >= W or Y >= H:
                        continue
                    j = Y * W + X
                    if lab[j] == -1 and walk[j]:
                        lab[j] = n
                        q.append(j)
        n += 1
    return lab, n


def snap(lab, w, h, wx, wy, maxr=40):
    W, H = w * 4, h * 4
    cx, cy = int(wx / 8), int(wy / 8)
    for r in range(0, maxr + 1):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                x, y = cx + dx, cy + dy
                if 0 <= x < W and 0 <= y < H and lab[y * W + x] >= 0:
                    return lab[y * W + x], r
    return -1, -1


rows = []
for line in open(os.path.join(ASSETS, "missions", "index.txt"), encoding="utf-8"):
    parts = [p.strip() for p in line.strip().split("|")]
    if len(parts) < 3 or not parts[0]:
        continue
    rows.append(parts[0])

cache = {}
for mid in rows:
    j = json.load(open(os.path.join(ASSETS, "missions", mid + ".json"), encoding="utf-8"))
    map_id = j["map"]
    if map_id not in cache:
        w, h, walk = read_walk(map_id)
        if walk is None:
            cache[map_id] = None
        else:
            lab, n = comps(w, h, walk)
            cache[map_id] = (w, h, lab, n)
    c = cache[map_id]
    if c is None:
        print("%-5s map=%-16s NO WALK" % (mid, map_id))
        continue
    w, h, lab, n = c

    hall = None
    for u in j.get("startUnits", []):
        if u.get("team", 0) == 0 and u["type"] in ("cc", "hatchery", "nexus"):
            hall = u
            break
    if hall is None:
        print("%-5s map=%-16s no player hall" % (mid, map_id))
        continue
    hc, hr = snap(lab, w, h, hall["x"], hall["y"])
    bad = []
    good = 0
    for u in j.get("startUnits", []):
        if u.get("team", 0) != 1:
            continue
        uc, ur = snap(lab, w, h, u["x"], u["y"])
        if uc != hc:
            bad.append("%s@(%d,%d) comp=%d r=%d" % (u["type"], u["x"], u["y"], uc, ur))
        else:
            good += 1
    for e in j.get("events", []):
        if e.get("action") != "wave":
            continue
        fr = e.get("from")
        if fr:
            fc, frr = snap(lab, w, h, fr[0], fr[1])
            if fc != hc:
                bad.append("wave-from(%d,%d) comp=%d r=%d" % (fr[0], fr[1], fc, frr))
            else:
                good += 1
        to = e.get("to")
        if to:
            tc, trr = snap(lab, w, h, to[0], to[1])
            if tc != hc:
                bad.append("wave-to(%d,%d) comp=%d r=%d" % (to[0], to[1], tc, trr))
            else:
                good += 1
    tag = "OK  " if not bad else "BAD "
    print("%s%-5s map=%-16s hallComp=%d r=%d comps=%d ok=%d bad=%d %s"
          % (tag, mid, map_id, hc, hr, n, good, len(bad), "; ".join(bad)))

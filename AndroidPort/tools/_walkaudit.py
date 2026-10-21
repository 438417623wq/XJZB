"""Audit every baked map: does the RUNTIME walk bitmap connect the starts?

pipeline_maps.connectivity() validates `_dilate(_fill_enclosed(walk), 1)` but
writes the RAW bitmap to walk.bin. This script checks the RAW bitmap that the
game actually loads, and compares the verdict with the island flag in meta.json.
"""
import gzip, glob, json, os, re
import numpy as np
from collections import deque

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"


def load_walk(mid):
    for name in ("walk.bin.gz", "walk.gz", "walk.bin"):
        p = os.path.join(ASSETS, mid, name)
        if os.path.exists(p):
            raw = gzip.open(p, "rb").read() if p.endswith(".gz") else open(p, "rb").read()
            return np.frombuffer(raw, dtype=np.uint8)
    return None


def read_meta(mid):
    p = os.path.join(ASSETS, mid, "meta.txt")
    d = {}
    for line in open(p, "r", encoding="utf-8", errors="replace"):
        line = line.strip()
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        d.setdefault(k, []).append(v)
    return d


def components(walk, H, W):
    lab = np.zeros((H, W), dtype=np.int32)
    c = 0
    for y in range(H):
        row = walk[y]
        for x in range(W):
            if row[x] and lab[y, x] == 0:
                c += 1
                dq = deque([(x, y)])
                lab[y, x] = c
                while dq:
                    cx, cy = dq.popleft()
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < W and 0 <= ny < H and walk[ny, nx] and lab[ny, nx] == 0:
                                lab[ny, nx] = c
                                dq.append((nx, ny))
    return lab, c


def snap(lab, walk, H, W, mx, my):
    if 0 <= mx < W and 0 <= my < H and walk[my, mx]:
        return int(lab[my, mx]), 0
    for r in range(1, 40):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                nx, ny = mx + dx, my + dy
                if 0 <= nx < W and 0 <= ny < H and walk[ny, nx]:
                    return int(lab[ny, nx]), r
    return None, None


rows = []
for d in sorted(os.listdir(ASSETS)):
    mp = os.path.join(ASSETS, d, "meta.txt")
    if not os.path.isdir(os.path.join(ASSETS, d)) or not os.path.exists(mp):
        continue
    meta = read_meta(d)
    w = int(meta["w"][0])
    h = int(meta["h"][0])
    starts = []
    for s in meta.get("start", []):
        sx, sy = s.split(",")[:2]
        starts.append((int(sx), int(sy)))
    walk = load_walk(d)
    if walk is None or len(walk) != w * 4 * h * 4:
        rows.append((d, w, h, len(starts), "NO-WALK", "-", "-", "-"))
        continue
    walk = walk.reshape(h * 4, w * 4) != 0
    lab, ncomp = components(walk, h * 4, w * 4)
    seeds = [snap(lab, walk, h * 4, w * 4, sx // 8, sy // 8) for sx, sy in starts]
    comps = [c for c, r in seeds]
    same = len(set(comps)) == 1
    js = os.path.join(ASSETS, d, "meta.json")
    island = "-"
    if os.path.exists(js):
        try:
            island = str(json.load(open(js, "r", encoding="utf-8")).get("island"))
        except Exception as e:
            island = "ERR"
    flag = "OK " if (same and island in ("0", "0.0")) or (not same and island in ("1", "1.0")) else "MISMATCH"
    rows.append((d, w, h, len(starts), "%d" % ncomp, "SAME" if same else "SPLIT",
                 str(comps), island, flag))

print("%-18s %4s %4s %3s %7s %6s %-22s %7s %s" % (
    "map", "w", "h", "st", "comps", "raw", "start comps", "island", "verdict"))
bad = 0
for r in rows:
    if len(r) == 5:
        print("%-18s %4s %4s %3s %7s" % r)
        continue
    d, w, h, st, nc, same, comps, island, flag = r
    if flag == "MISMATCH":
        bad += 1
    print("%-18s %4d %4d %3d %7s %6s %-22s %7s %s" % (d, w, h, st, nc, same, comps, island, flag))
print()
print("maps=%d  mismatches=%d" % (len(rows), bad))

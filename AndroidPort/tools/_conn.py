"""v2.44 evidence: are the two starts of each map in the same walkable component?

The AI wave report claims divide's player CC and the enemy hatchery sit in two
different components, so no ground path can ever exist. That is a P0 claim, so
re-derive it here straight from walk.bin.gz instead of trusting the report.
"""
import gzip
import json
import os
import sys
from collections import deque

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"


def load_walk(mid):
    p = os.path.join(ASSETS, mid, "walk.bin.gz")
    with gzip.open(p, "rb") as f:
        raw = f.read()
    with open(os.path.join(ASSETS, mid, "meta.txt"), "r", encoding="utf-8") as f:
        meta = {}
        for line in f:
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                meta.setdefault(k, []).append(v)
    w = int(meta["w"][0])
    h = int(meta["h"][0])
    starts = [[int(x) for x in s.split(",")] for s in meta["start"]]
    return raw, w, h, starts


def main():
    ids = sorted(d for d in os.listdir(ASSETS)
                 if os.path.isdir(os.path.join(ASSETS, d)))
    for mid in ids:
        try:
            raw, w, h, starts = load_walk(mid)
        except Exception as e:
            print("%-18s SKIP %s" % (mid, e))
            continue
        mw, mh = w * 4, h * 4
        if len(raw) != mw * mh:
            print("%-18s size mismatch raw=%d expect=%d" % (mid, len(raw), mw * mh))
            continue
        walk = bytes(1 if b else 0 for b in raw)
        # label components with an 8-connected flood fill
        label = [-1] * (mw * mh)
        comp = 0
        sizes = []
        for i in range(mw * mh):
            if walk[i] == 0 or label[i] != -1:
                continue
            q = deque([i])
            label[i] = comp
            n = 0
            while q:
                c = q.popleft()
                n += 1
                cx, cy = c % mw, c // mw
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = cx + dx, cy + dy
                        if nx < 0 or ny < 0 or nx >= mw or ny >= mh:
                            continue
                        ni = ny * mw + nx
                        if walk[ni] == 0 or label[ni] != -1:
                            continue
                        label[ni] = comp
                        q.append(ni)
            sizes.append(n)
            comp += 1
        # snap each start to its nearest walkable minitile
        def comp_of(px, py):
            mx, my = int(px) // 8, int(py) // 8
            best = None
            for r in range(0, 64):
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        if max(abs(dx), abs(dy)) != r:
                            continue
                        nx, ny = mx + dx, my + dy
                        if 0 <= nx < mw and 0 <= ny < mh and walk[ny * mw + nx]:
                            return label[ny * mw + nx], (nx, ny), r
            return None, None, None

        res = [comp_of(s[0], s[1]) for s in starts]
        same = len(set(r[0] for r in res)) == 1
        big = sorted(sizes, reverse=True)[:4]
        print("%-18s %dx%d tile  comps=%d top=%s  starts=%s  SAME=%s"
              % (mid, w, h, comp, big,
                 [(r[0], r[2]) for r in res], same))


main()

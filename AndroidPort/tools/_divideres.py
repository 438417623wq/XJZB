"""v2.44: what is on divide's player component, resource-wise?

Before moving m01's enemy base onto the player's landmass, check that the
landmass is actually a playable base: minerals, a geyser, and room for the
enemy cluster without overlapping the player's own start.
"""
import gzip
import os

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
MAP = os.path.join(ASSETS, "maps", "divide")

with open(os.path.join(MAP, "meta.txt"), "r", encoding="utf-8", errors="replace") as f:
    meta = f.read()
W = H = 0
starts = []
units = []
for line in meta.splitlines():
    if line.startswith("w="):
        W = int(line[2:])
    elif line.startswith("h="):
        H = int(line[2:])
    elif line.startswith("start="):
        a, b = line[6:].split(",")
        starts.append((int(a), int(b)))
    elif line.startswith("unit="):
        p = line[5:].split(",")
        units.append((int(p[0]), int(p[1]), int(p[2]), int(p[3]), int(p[4]), int(p[5])))

with gzip.open(os.path.join(MAP, "walk.bin.gz"), "rb") as f:
    raw = f.read()
MW, MH = W * 4, H * 4
walk = [b != 0 for b in raw]


def wm(mx, my):
    return 0 <= mx < MW and 0 <= my < MH and walk[my * MW + mx]


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
print("divide %dx%d tiles, starts=%s" % (W, H, starts))
print("player comp%d size=%d" % (pcomp, comps[pcomp]))
print()
print("== map units (kind, x, y, ?, ?, variant)")
KIND = {0: "unit?", 1: "mineral", 2: "geyser"}
for u in units:
    k, x, y, a, b, v = u
    c = comp[(y // 8) * MW + (x // 8)]
    same = "PLAYER-COMP" if c == pcomp else ""
    print("   kind=%d %-8s @(%4d,%4d) a=%d b=%d var=%d comp=%d %s"
          % (k, KIND.get(k, "?"), x, y, a, b, v, c, same))

print()
print("== resource counts per component (components >1000 minitiles)")
from collections import Counter
cnt = Counter()
for k, x, y, a, b, v in units:
    c = comp[(y // 8) * MW + (x // 8)]
    if k == 1:
        cnt[("mineral", c)] += 1
    elif k == 2:
        cnt[("geyser", c)] += 1
for i, size in enumerate(comps):
    if size <= 1000:
        continue
    print("   comp%d size=%-6d minerals=%-3d geysers=%d"
          % (i, size, cnt[("mineral", i)], cnt[("geyser", i)]))

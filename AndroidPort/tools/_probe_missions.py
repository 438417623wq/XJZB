import gzip, os, json, glob, heapq, collections, re

ROOT = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
MAPS = os.path.join(ROOT, "maps")
MISS = os.path.join(ROOT, "missions")

def read_meta(mid):
    txt = open(os.path.join(MAPS, mid, "meta.txt"), encoding="utf-8").read()
    d = {}
    starts = []
    for line in txt.splitlines():
        if line.startswith("start="):
            a, b = line[6:].split(","); starts.append((int(a), int(b)))
        elif "=" in line:
            k, v = line.split("=", 1); d[k] = v
    return int(d["w"]), int(d["h"]), starts

def load_walk(mid, wT, hT):
    for n in ("walk.bin.gz", "walk.gz"):
        p = os.path.join(MAPS, mid, n)
        if os.path.exists(p):
            raw = gzip.open(p, "rb").read()
            if len(raw) == wT * 4 * hT * 4: return raw
            print(f"    !! {mid}/{n} size {len(raw)} != {wT*4*hT*4}")
            return raw
    p = os.path.join(MAPS, mid, "walk.bin")
    return open(p, "rb").read()

def build(walk, wMini, hMini):
    def pm(x, y): return 0 <= x < wMini and 0 <= y < hMini and walk[y * wMini + x] != 0
    return pm

def nearest(pm, x, y, maxR=24):
    for r in range(0, maxR + 1):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r: continue
                if pm(x + dx, y + dy): return (x + dx, y + dy)
    return None

DX = [1, -1, 0, 0, 1, 1, -1, -1]; DY = [0, 0, 1, -1, 1, -1, 1, -1]

def find_path(pm, wMini, hMini, sx, sy, gx, gy, cap=60000):
    approx = False
    if not pm(gx, gy):
        alt = nearest(pm, gx, gy, 24)
        if alt is None: return None, True, 0
        gx, gy = alt; approx = True
    if not pm(sx, sy):
        alt = nearest(pm, sx, sy, 24)
        if alt is None: return None, True, 0
        sx, sy = alt
    def heur(x, y):
        dx, dy = abs(x - gx), abs(y - gy)
        return (dx + dy) + (1.4142 - 2.0) * min(dx, dy)
    n = wMini * hMini
    g = [float("inf")] * n; fr = [-1] * n; closed = [False] * n
    start = sy * wMini + sx; goal = gy * wMini + gx
    g[start] = 0; h = [(heur(sx, sy), start)]; exp = 0; found = -1
    while h and exp < cap:
        f, cur = heapq.heappop(h)
        if closed[cur]: continue
        closed[cur] = True; exp += 1
        if cur == goal: found = cur; break
        cx, cy = cur % wMini, cur // wMini
        for d in range(8):
            nx, ny = cx + DX[d], cy + DY[d]
            if not pm(nx, ny): continue
            if d >= 4 and (not pm(cx + DX[d], cy) or not pm(cx, cy + DY[d])): continue
            ni = ny * wMini + nx
            if closed[ni]: continue
            ng = g[cur] + (1.4142 if d >= 4 else 1.0)
            if ng < g[ni]:
                g[ni] = ng; fr[ni] = cur
                heapq.heappush(h, (ng + heur(nx, ny), ni))
    if found < 0: return None, True, exp
    nodes = 0; c = found
    while c != -1:
        nodes += 1
        if c == start: break
        c = fr[c]
    return nodes, approx, exp

def label8(walk, wMini, hMini):
    lab = [-1] * (wMini * hMini); sizes = []
    for i in range(wMini * hMini):
        if walk[i] == 0 or lab[i] != -1: continue
        cid = len(sizes); lab[i] = cid; q = collections.deque([i]); n = 0
        while q:
            cur = q.popleft(); n += 1
            cx, cy = cur % wMini, cur // wMini
            for d in range(8):
                nx, ny = cx + DX[d], cy + DY[d]
                if 0 <= nx < wMini and 0 <= ny < hMini:
                    ni = ny * wMini + nx
                    if walk[ni] and lab[ni] == -1: lab[ni] = cid; q.append(ni)
        sizes.append(n)
    return lab, sizes

print(f"{'mission':8s} {'map':16s} {'mapWxH':9s} {'cmps':4s} {'cc_comp':7s} {'hatch_comp':10s} "
      f"{'same':5s} {'A*find':7s} {'expans':7s} {'hatch_world':14s} {'cc_world':12s}")
print("-" * 128)

for mf in sorted(glob.glob(os.path.join(MISS, "*.json"))):
    j = json.load(open(mf, encoding="utf-8"))
    mid = j["id"]; mp = j["map"]
    wT, hT, starts = read_meta(mp)
    walk = load_walk(mp, wT, hT); wMini, hMini = wT * 4, hT * 4
    pm = build(walk, wMini, hMini)
    lab, sizes = label8(walk, wMini, hMini)

    cc = starts[0]
    # team-1 hatchery from startUnits
    hatch = None
    for su in j.get("startUnits", []):
        # format likely {"team":1,"type":"hatchery","x":..,"y":..}
        if isinstance(su, dict) and su.get("type") == "hatchery" and su.get("team") == 1:
            hatch = (su["x"], su["y"]); break
        if isinstance(su, dict) and su.get("type") == "hatchery" and hatch is None:
            hatch = (su["x"], su["y"])
    if hatch is None:
        for su in j.get("startUnits", []):
            if isinstance(su, dict) and "hatchery" in json.dumps(su):
                hatch = (su.get("x", 0), su.get("y", 0)); break
    if hatch is None:
        print(f"{mid:8s} {mp:16s} NO HATCHERY IN startUnits")
        continue

    cm = nearest(pm, cc[0] // 8, cc[1] // 8, 24)
    hm = nearest(pm, hatch[0] // 8, hatch[1] // 8, 24)
    ccC = lab[cm[1] * wMini + cm[0]] if cm else -1
    hC = lab[hm[1] * wMini + hm[0]] if hm else -1
    nodes, approx, exp = find_path(pm, wMini, hMini, hm[0], hm[1], cm[0], cm[1])
    print(f"{mid:8s} {mp:16s} {wT}x{hT:<6} {len(sizes):<4d} {ccC:<7d} {hC:<10d} "
          f"{str(ccC == hC):5s} {str(nodes is not None):7s} {exp:<7d} "
          f"{str(hatch):14s} {str(cc):12s}")

import gzip, os, collections

MAPS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"

def load(mid, wT, hT):
    raw = gzip.open(os.path.join(MAPS, mid, "walk.bin.gz"), "rb").read()
    return raw, wT * 4, hT * 4

def components(walk, wMini, hMini, diag=True):
    """label connected components; diag=False -> 4-connected"""
    lab = [-1] * (wMini * hMini)
    comps = []
    D4 = ((1,0),(-1,0),(0,1),(0,-1))
    D8 = D4 + ((1,1),(1,-1),(-1,1),(-1,-1))
    D = D8 if diag else D4
    for i in range(wMini * hMini):
        if walk[i] == 0 or lab[i] != -1: continue
        cid = len(comps); lab[i] = cid; q = collections.deque([i]); cells = 0
        while q:
            cur = q.popleft(); cells += 1
            cx, cy = cur % wMini, cur // wMini
            for dx, dy in D:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < wMini and 0 <= ny < hMini:
                    ni = ny * wMini + nx
                    if walk[ni] and lab[ni] == -1:
                        lab[ni] = cid; q.append(ni)
        comps.append(cells)
    return lab, comps

for mid, wT, hT in (("divide", 64, 64),):
    walk, wMini, hMini = load(mid, wT, hT)
    lab4, c4 = components(walk, wMini, hMini, diag=False)
    lab8, c8 = components(walk, wMini, hMini, diag=True)
    print(f"=== {mid} {wMini}x{hMini} ===")
    print(f"  4-connected components: {len(c4)}  sizes(desc)={sorted(c4,reverse=True)[:8]}")
    print(f"  8-connected components: {len(c8)}  sizes(desc)={sorted(c8,reverse=True)[:8]}")

    pts = {
        "player_start(320,240)": (320, 240),
        "enemy_hatchery(1728,1776)": (1728, 1776),
        "m01_from(1500,1500)": (1500, 1500),
        "m01_to(420,300)": (420, 300),
        "pool(1568,1846)": (1568, 1846),
    }
    for name, (wx, wy) in pts.items():
        mx, my = wx // 8, wy // 8
        i = my * wMini + mx
        print(f"  {name:28s} mini=({mx},{my}) walk={walk[i]!=0} comp4={lab4[i]} comp8={lab8[i]}")

    # bounding boxes of the two biggest 8-connected components
    for cid in range(min(4, len(c8))):
        xs = [i % wMini for i in range(len(lab8)) if lab8[i] == cid]
        ys = [i // wMini for i in range(len(lab8)) if lab8[i] == cid]
        if not xs: continue
        print(f"  comp8 #{cid}: {c8[cid]} tiles  bbox mini x[{min(xs)},{max(xs)}] y[{min(ys)},{max(ys)}]"
              f"  = world px x[{min(xs)*8},{max(xs)*8}] y[{min(ys)*8},{max(ys)*8}]")

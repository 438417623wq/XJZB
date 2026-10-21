import gzip, os, collections

MAPS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"
mid = "divide"
wT = hT = 64
raw = gzip.open(os.path.join(MAPS, mid, "walk.bin.gz"), "rb").read()
wMini, hMini = wT * 4, hT * 4
walk = raw

DX = [1,-1,0,0,1,1,-1,-1]; DY = [0,0,1,-1,1,-1,1,-1]
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

print(f"{mid}: {len(sizes)} 8-connected landmasses, sizes desc = {sorted(sizes, reverse=True)}")
print("landmass id -> size, bbox(mini), bbox(world px):")
for cid in sorted(range(len(sizes)), key=lambda c: -sizes[c]):
    idx = [i for i in range(len(lab)) if lab[i] == cid]
    xs = [i % wMini for i in idx]; ys = [i // wMini for i in idx]
    print(f"  #{cid:<3d} size={sizes[cid]:<6d} mini x[{min(xs)},{max(xs)}] y[{min(ys)},{max(ys)}]"
          f"   px x[{min(xs)*8},{max(xs)*8}] y[{min(ys)*8},{max(ys)*8}]")

MARK = {
    (320, 240): "P",      # player cc
    (470, 270): "B",      # player barracks
    (1728, 1776): "H",    # enemy hatchery
    (1568, 1846): "h",    # enemy pool
    (1500, 1500): "F",    # m01 scripted wave spawn point
    (420, 300): "T",      # m01 scripted wave destination
    (1450, 1450): "G",    # m01 wave 3 spawn
}

# ASCII render: sample 4x4 minitiles per char => 64x64 chars
print()
print("ASCII map (1 char = 1 tile = 4x4 minitiles). '.'=walkable, '#'=blocked, digit=landmass id")
print("    " + "".join(str((c // 10) % 10) for c in range(0, wT, 1)))
hdr = "    " + "".join(str(c % 10) for c in range(wT))
print(hdr)
for ty in range(hT):
    row = []
    for tx in range(wT):
        # find mark in this tile
        mk = "."
        for (wx, wy), ch in MARK.items():
            if wx // 32 == tx and wy // 32 == ty:
                mk = ch; break
        if mk != ".":
            row.append(mk); continue
        # landmass id of the centre minitile
        mx, my = tx * 4 + 2, ty * 4 + 2
        i = my * wMini + mx
        row.append("#" if walk[i] == 0 else str(lab[i] % 10))
    print(f"{ty:3d} " + "".join(row))
print()
print("legend: P=player cc(320,240) B=barracks T=scripted-wave target(420,300)")
print("        H=enemy hatchery(1728,1776) h=pool F=scripted-wave spawn(1500,1500) G=wave3 spawn(1450,1450)")

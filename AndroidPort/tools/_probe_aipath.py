import gzip, heapq, os, sys

MAPS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"

def load_walk(mid, wTiles, hTiles):
    p = os.path.join(MAPS, mid, "walk.bin.gz")
    raw = gzip.open(p, "rb").read()
    exp = wTiles * 4 * hTiles * 4
    print(f"[{mid}] walk raw={len(raw)} expect={exp} match={len(raw)==exp}")
    return raw

def find_path(walk, wMini, hMini, sx, sy, gx, gy, cap=60000, verbose=False):
    def passMini(x, y):
        return 0 <= x < wMini and 0 <= y < hMini and walk[y * wMini + x] != 0
    def nearest(x, y, maxR):
        for r in range(1, maxR + 1):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r: continue
                    if passMini(x + dx, y + dy): return (x + dx, y + dy)
        return None
    approx = False
    if not passMini(gx, gy):
        alt = nearest(gx, gy, 24)
        if alt is None: return None, True, 0
        gx, gy = alt; approx = True
    DX = [1, -1, 0, 0, 1, 1, -1, -1]
    DY = [0, 0, 1, -1, 1, -1, 1, -1]
    def heur(x, y):
        dx, dy = abs(x - gx), abs(y - gy)
        return (dx + dy) + (1.4142 - 2.0) * min(dx, dy)
    n = wMini * hMini
    g = [float("inf")] * n
    fr = [-1] * n
    closed = [False] * n
    start = sy * wMini + sx; goal = gy * wMini + gx
    if not passMini(sx, sy):
        a2 = nearest(sx, sy, 24)
        if a2 is None: return None, True, 0
        start = a2[1] * wMini + a2[0]
    g[start] = 0
    h = [(heur(sx, sy), start)]
    exp = 0; found = -1
    while h and exp < cap:
        f, cur = heapq.heappop(h)
        if closed[cur]: continue
        closed[cur] = True
        exp += 1
        if cur == goal:
            found = cur; break
        cx, cy = cur % wMini, cur // wMini
        for d in range(8):
            nx, ny = cx + DX[d], cy + DY[d]
            if not passMini(nx, ny): continue
            if d >= 4 and (not passMini(cx + DX[d], cy) or not passMini(cx, cy + DY[d])): continue
            ni = ny * wMini + nx
            if closed[ni]: continue
            step = 1.4142 if d >= 4 else 1.0
            ng = g[cur] + step
            if ng < g[ni]:
                g[ni] = ng; fr[ni] = cur
                heapq.heappush(h, (ng + heur(nx, ny), ni))
    if found < 0:
        return None, True, exp
    return found, approx, exp

def reachable(walk, wMini, hMini, sx, sy):
    """full flood fill - ground truth connectivity"""
    if walk[sy * wMini + sx] == 0: return set()
    seen = {sy * wMini + sx}; stack = [(sx, sy)]
    while stack:
        x, y = stack.pop()
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < wMini and 0 <= ny < hMini and walk[ny * wMini + nx] and (ny*wMini+nx) not in seen:
                seen.add(ny * wMini + nx); stack.append((nx, ny))
    return seen

for mid, wT, h_T in (("divide", 64, 64),):
    walk = load_walk(mid, wT, h_T)
    wMini, hMini = wT * 4, h_T * 4
    print(f"  wMini={wMini} hMini={hMini} n={wMini*hMini} walkable={sum(1 for b in walk if b)}")

    # m01: player start 320,240 ; enemy hatchery 1728,1776 (world px)
    P = (320 // 8, 240 // 8)
    H = (1728 // 8, 1776 // 8)
    print(f"  player start mini={P} pass={walk[P[1]*wMini+P[0]]!=0}")
    print(f"  enemy hatch  mini={H} pass={walk[H[1]*wMini+H[0]]!=0}")

    # player CC actual footprint centre: start=320,240 is a start loc; CC is 4x4 tiles=32px
    # find nearest passable to CC
    def nearest(x, y, maxR):
        for r in range(0, maxR+1):
            for dy in range(-r, r+1):
                for dx in range(-r, r+1):
                    if max(abs(dx),abs(dy)) != r: continue
                    if 0<=x+dx<wMini and 0<=y+dy<hMini and walk[(y+dy)*wMini+(x+dx)]: return (x+dx,y+dy)
        return None
    Pn = nearest(*P, 24); Hn = nearest(*H, 24)
    print(f"  nearest-pass player={Pn} enemy={Hn}")

    reach = reachable(walk, wMini, hMini, *Pn)
    print(f"  flood-fill from player start reaches {len(reach)} minitiles; enemy hatch in same component? {Hn[1]*wMini+Hn[0] in reach}")

    found, approx, exp = find_path(walk, wMini, hMini, Hn[0], Hn[1], Pn[0], Pn[1])
    print(f"  findPath enemy->player: found={found is not None} approx={approx} expansions={exp} (cap 60000)")

    found2, approx2, exp2 = find_path(walk, wMini, hMini, Pn[0], Pn[1], Hn[0], Hn[1])
    print(f"  findPath player->enemy: found={found2 is not None} approx={approx2} expansions={exp2}")

    # scripted m01 wave: from (1500,1500) to (420,300)
    F = nearest(1500//8, 1500//8, 24); T = nearest(420//8, 300//8, 24)
    f3, a3, e3 = find_path(walk, wMini, hMini, F[0], F[1], T[0], T[1])
    print(f"  findPath m01 scripted (1500,1500)->(420,300): found={f3 is not None} approx={a3} expansions={e3}")
    print(f"    from={F} pass={walk[F[1]*wMini+F[0]]!=0} to={T} pass={walk[T[1]*wMini+T[0]]!=0}")

    # how far does the A* get before the cap? measure best-effort progress
    # count how many minitiles are passable total
    print(f"  total walkable minitiles on map: {sum(1 for b in walk if b)}")

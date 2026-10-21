"""Final map pipeline: .scm -> terrain chunks + walkability + units JSON.

Chain: MTXM u16 = (group << 4) | variant -> CV5[group] @20 u16[16] = VX4
megatile[var] -> 16x (bit0 flip | VR4 id = e >> 1) -> 64B 8bpp minitiles.
Walkability: VF4[vr4Index] bit 0. (Validated via start-connectivity on Blood Bath.)
"""
import json
import os
import struct
import zlib
from collections import deque

import numpy as np
from PIL import Image

import sc_archive

# v2.16 batch 3.1: start-connectivity gate. The port has no dropship/landing
# mechanic, so a map whose start locations sit on separate landmasses is a
# dead game no matter how pretty it looks -- the enemy can never be reached.
# The check runs BEFORE any human map pick, narrowing the 153-map disk pool to
# a "playable pool" first (Island Hop / Sapphire Isles / Primeval Isles are
# exactly what this is meant to drop).
#
# The walkability read is unchanged (VF4 bit 0 of minitile k of the megatile
# CV5[group][variant] points at), but the raw bitmap is fragmented by hairline
# cliff tiles and 1-cell ramp mouths. The gate relaxes it the two ways a
# pathfinder does at run time: 8-connectivity (a diagonal step through a ramp
# mouth is a legal move) and a 1-cell dilation that closes the single-minitile
# holes those tiles leave. Islands stay separated under both -- their water is
# many cells wide -- so the test still rejects exactly the maps the plan wants.
GATE_DILATE = 1

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(ROOT, r"AndroidPort\app\app\src\main\assets")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))

# Standard StarCraft tileset ids as stored in the CHK MTXM/DIM header. The
# old table shifted 2-6 down by one and had no entry for 7, so every map from
# jungle onward rendered with the wrong palette (jungle maps got desert, and
# ashworld maps got jungle).
TILESETS = {0: "badlands", 1: "platform", 2: "install", 3: "ashworld",
            4: "jungle", 5: "desert", 6: "ice", 7: "twilight"}
MINERAL_IDS = {176, 177, 178}
GEYSER_ID = 188
START_ID = 214
CHUNK = 512

_ts_cache = {}


def load_tileset(ts):
    if ts in _ts_cache:
        return _ts_cache[ts]
    def rd(n):
        for ar in (SD, BD):
            if ar.has("tileset\\%s.%s" % (ts, n)):
                return ar.read_with_gaps("tileset\\%s.%s" % (ts, n))
        return None, None
    wpe, _ = rd("wpe")
    if wpe is None:
        _ts_cache[ts] = None
        return None
    if len(wpe) < 1024:
        wpe += bytes(1024 - len(wpe))
    # WPE entries are R,G,B,0 -- see pipeline_sprites.py for why the old
    # back-to-front read swapped red and blue across every map.
    pal = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]
    cv5, g0 = rd("cv5")
    vx4, g2 = rd("vx4")
    vr4, g3 = rd("vr4")
    vf4, g4 = rd("vf4")
    from gapio import GapReader
    gc, gv, gr, gf = (GapReader(cv5, g0 or []), GapReader(vx4, g2 or []),
                      GapReader(vr4, g3 or []), GapReader(vf4, g4 or []))
    # Counts must use the gap-restored length: read_with_gaps returns the short
    # buffer plus a gap list, so len(cv5)//52 undercounts by the number of
    # structs the repack dropped (platform 1507 vs 1513).
    def _count(buf, gaps, size):
        return (len(buf) + sum(s for _, s in (gaps or []))) // size
    n_mega = _count(cv5, g0, 52)
    # CV5 struct is 52 B: @0 terrain type, @2 flags, @4 u16[4] edge types,
    # @12 u16[4] terrain piece types, @20 u16[16] VX4 megatile refs. MTXM packs
    # a tile as (group << 4) | variant, so the megatile to draw is
    # cv5_tiles[group][variant]. Reading @0 (the terrain type) as a megatile
    # index -- which this did -- paints void tiles across every map.
    cv5_tiles = [[gc.u16(m * 52 + 20 + k * 2) for k in range(16)]
                 for m in range(n_mega)]
    cv5_type = [gc.u16(m * 52) for m in range(n_mega)]
    mega_vx4 = cv5_tiles
    n_vx4 = _count(vx4, g2, 32)
    # vx4 megatile m = 16 u16 refs
    vx4_refs = [[gv.u16(m * 32 + k * 2) for k in range(16)] for m in range(n_vx4)]
    # VF4 is exactly parallel to VX4 (same file size, 32 B per megatile): each
    # megatile has 16 u16 minitile flag words, and bit 0 of minitile k is that
    # minitile's walkability. The old read treated the file as one u32 per VR4
    # image, so it sampled an unrelated megatile's flags for every minitile.
    n_flag = _count(vf4, g4, 32)
    vf4_flags = [[gf.u16(m * 32 + k * 2) for k in range(16)] for m in range(n_flag)]
    n_pix = _count(vr4, g3, 64)
    pixels = [gr.bytes_at(m * 64, 64) for m in range(n_pix)]
    _ts_cache[ts] = {"pal": pal, "mega_vx4": mega_vx4, "cv5_tiles": cv5_tiles,
                     "cv5_type": cv5_type, "vx4_refs": vx4_refs,
                     "vf4_flags": vf4_flags, "pixels": pixels, "name": ts}
    return _ts_cache[ts]


def parse_chk(chk, gaps):
    from gapio import GapReader
    g = GapReader(chk, gaps)
    orig_len = len(chk) + sum(s for _, s in gaps)
    valid = set(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ ")
    sections = {}
    p = 0
    while p + 8 <= orig_len:
        tag = g.bytes_at(p, 4)
        size = g.u32(p + 4)
        if not all(c in valid for c in tag):
            p += 1
            continue
        if size < 0 or p + 8 + size > orig_len:
            p += 1
            continue
        sections[tag] = (p + 8, size)
        p += 8 + size
    return g, sections


def read_chk(scm_path):
    try:
        ar = sc_archive.Archive(scm_path)
    except Exception:
        return None
    if ar.has("staredit\\scenario.chk"):
        return ar.read_with_gaps("staredit\\scenario.chk")
    return None


# --------------------------------------------------- v2.16 batch 3.1: gate

def _walk_bitmap(w, h, mtwm, ts):
    """The shipped walkability read, vectorised with numpy.

    Returns a (h*4, w*4) uint8 array where 1 = walkable. Same chain as
    build_map: MTXM -> CV5[group][variant] -> VF4[that megatile] bit 0 per
    minitile. Vectorising it turns the 153-map census from ~20 minutes into
    seconds, which is what makes the gate practical to run on every build.
    """
    m = np.asarray(mtwm, dtype=np.uint32).reshape(h, w)
    grp = (m & 0x7FF0) >> 4
    var = m & 0xF
    tiles = np.asarray(ts["cv5_tiles"], dtype=np.int64)      # [n_cv5][16]
    grp = np.clip(grp, 0, len(tiles) - 1)
    vx4m = tiles[grp, var]                                   # [h][w]
    # Replicate the scalar loop's two guards exactly: an out-of-range vx4m
    # falls back to 0, and a megatile with no VF4 entry contributes no flags.
    # (Getting this wrong shifts a handful of minitiles on the maps whose
    # VF4 table is shorter than their VX4 table -- Volcanis, River Lethe.)
    n_ref = len(ts["vx4_refs"])
    vx4m = np.where(vx4m >= n_ref, 0, vx4m)
    flags = np.asarray(ts["vf4_flags"], dtype=np.int64)      # [n_vx4][16]
    if len(flags) == 0:
        return np.zeros((h * 4, w * 4), dtype=np.uint8)
    valid = vx4m < len(flags)
    f = flags[np.clip(vx4m, 0, len(flags) - 1)]              # [h][w][16]
    f = np.where(valid[..., None], f, 0)
    f = f.reshape(h, w, 4, 4)                                # k = row*4+col
    return (f & 1).astype(np.uint8).transpose(0, 2, 1, 3).reshape(h * 4, w * 4)


def _elev_bitmap(w, h, mtwm, ts):
    """v2.23 batch C: the per-minitile ground level, 0 low / 1 mid / 2 high.

    Same decode chain as _walk_bitmap, reading VF4 flag bit 1 (MidGround,
    0x0002) and bit 2 (HighGround, 0x0004). Bit 0 is walkability, bit 3 is
    "blocks view" and bit 4 is the ramp flag. The bit layout is the
    community-documented one, cross-checked three ways before this shipped:
    the level boundary of walkable ground lands on ramp tiles 76-100% of the
    time across the shipped maps, the level regions are large and contiguous,
    and the CV5 group ground height agrees with the per-minitile value. See
    the v2.23 batch C notes in the progress report.
    """
    m = np.asarray(mtwm, dtype=np.uint32).reshape(h, w)
    grp = (m & 0x7FF0) >> 4
    var = m & 0xF
    tiles = np.asarray(ts["cv5_tiles"], dtype=np.int64)
    grp = np.clip(grp, 0, len(tiles) - 1)
    vx4m = tiles[grp, var]
    n_ref = len(ts["vx4_refs"])
    vx4m = np.where(vx4m >= n_ref, 0, vx4m)
    flags = np.asarray(ts["vf4_flags"], dtype=np.int64)
    if len(flags) == 0:
        return np.zeros((h * 4, w * 4), dtype=np.uint8)
    valid = vx4m < len(flags)
    f = flags[np.clip(vx4m, 0, len(flags) - 1)]
    f = np.where(valid[..., None], f, 0)
    f = f.reshape(h, w, 4, 4)
    lvl = np.where((f & 4) != 0, 2, np.where((f & 2) != 0, 1, 0))
    return lvl.astype(np.uint8).transpose(0, 2, 1, 3).reshape(h * 4, w * 4)


def _starts_of(g, sec):
    """Start-location pixels (CHK stores them at 8x the minitile grid)."""
    starts = []
    if b"UNIT" in sec:
        off, size = sec[b"UNIT"]
        for i in range(size // 36):
            base = off + i * 36
            if g.u16(base + 8) == START_ID:
                starts.append((g.u16(base + 4) // 8, g.u16(base + 6) // 8))
    return starts


def _fill_enclosed(walk):
    """Flood the walkable cells from the border; any unwalkable cell the
    border flood never reached is an enclosed pocket and becomes walkable.

    The damaged repack leaves single-minitile holes in the VF4 read (see the
    header note), and a hole in the middle of a ramp reads as a wall even
    though the ramp is wide open. Filling only *enclosed* pockets cannot merge
    two landmasses -- the sea is connected to the map border, so it is never
    filled.
    """
    H, W = walk.shape
    out = walk.astype(bool).copy()
    seen = np.zeros((H, W), dtype=bool)
    dq = deque()
    for x in range(W):
        for y in (0, H - 1):
            if not out[y, x] and not seen[y, x]:
                seen[y, x] = True
                dq.append((y, x))
    for y in range(H):
        for x in (0, W - 1):
            if not out[y, x] and not seen[y, x]:
                seen[y, x] = True
                dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W and not out[yy, xx] and not seen[yy, xx]:
                seen[yy, xx] = True
                dq.append((yy, xx))
    out[~seen] = True
    return out.astype(np.uint8)


def _dilate(walk, r):
    """Square dilation by r minitiles. r=1 closes a hairline cliff seam; it is
    far too small to bridge an island's water."""
    if r <= 0:
        return walk
    out = walk.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= np.roll(np.roll(walk, dy, axis=0), dx, axis=1)
    return out


def connectivity(walk, starts, dilate=GATE_DILATE):
    """True when every start location is reachable from every other one.

    One 8-connected flood fill from the first start; each later start must be
    inside that filled set. Single-source keeps the gate fast enough to run on
    all 153 maps (a per-start fill would re-walk the same component).
    """
    if len(starts) < 2:
        return False, []
    wk = _dilate(_fill_enclosed(walk), dilate)
    H, W = wk.shape

    def snap(sx, sy):
        for rr in range(0, 40):
            y0, y1 = max(0, sy - rr), min(H, sy + rr + 1)
            x0, x1 = max(0, sx - rr), min(W, sx + rr + 1)
            sub = wk[y0:y1, x0:x1]
            if sub.any():
                ys, xs = np.nonzero(sub)
                return int(y0 + ys[0]), int(x0 + xs[0])
        return None

    seeds = [snap(sx, sy) for sx, sy in starts]
    if seeds[0] is None:
        return False, seeds
    seen = np.zeros((H, W), dtype=bool)
    dq = deque([seeds[0]])
    seen[seeds[0]] = True
    nbr = ((1, 0), (-1, 0), (0, 1), (0, -1),
           (1, 1), (1, -1), (-1, 1), (-1, -1))
    while dq:
        y, x = dq.popleft()
        for dy, dx in nbr:
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W and wk[yy, xx] and not seen[yy, xx]:
                seen[yy, xx] = True
                dq.append((yy, xx))
    ok = all(s is not None and seen[s] for s in seeds)
    return ok, [None if s is None else (0 if seen[s] else 1) for s in seeds]


def _snap_nearest(walk, sx, sy, max_r=24):
    """nearestPassMini mirror: the closest walkable minitile within max_r,
    None when the pocket is sealed deeper than that. The engine snaps goals
    (and indirectly spawns) through this lens, so every connectivity verdict
    must snap through the same one -- a looser snap "proved" divide connected
    while its bases sat in two different components."""
    H, W = walk.shape
    best = None
    bd = None
    for r in range(0, max_r + 1):
        y0, y1 = max(0, sy - r), min(H, sy + r + 1)
        x0, x1 = max(0, sx - r), min(W, sx + r + 1)
        ys, xs = np.nonzero(walk[y0:y1, x0:x1])
        for yy, xx in zip(ys, xs):
            d = (int(xx) + x0 - sx) ** 2 + (int(yy) + y0 - sy) ** 2
            if bd is None or d < bd:
                bd = d
                best = (int(yy) + y0, int(xx) + x0)
        if best is not None:
            return best
    return best


def reachable(walk, starts):
    """v2.44: the connectivity verdict on the EXACT bitmap, with no relaxation.

    `connectivity()` above deliberately relaxes (fill + dilate) because the
    census runs on raw CHK reads. This function is the one that must agree
    with the game: the bytes passed in are the bytes walk.bin ships and the
    only thing A* gets, so the fill/dilate crutches are OFF -- a start is
    reachable iff an 8-connected walkable path exists between the
    nearestPassMini-snapped starts, exactly like the engine's findPath (which
    also forbids cutting a diagonal corner).
    """
    if len(starts) < 2:
        return False
    H, W = walk.shape

    seed = _snap_nearest(walk, *starts[0])
    if seed is None:
        return False
    seen = np.zeros((H, W), dtype=bool)
    dq = deque([seed])
    seen[seed] = True
    orth = ((1, 0), (-1, 0), (0, 1), (0, -1))
    diag = ((1, 1), (1, -1), (-1, 1), (-1, -1))
    while dq:
        y, x = dq.popleft()
        for dy, dx in orth:
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W and walk[yy, xx] and not seen[yy, xx]:
                seen[yy, xx] = True
                dq.append((yy, xx))
        for dy, dx in diag:
            yy, xx = y + dy, x + dx
            if not (0 <= yy < H and 0 <= xx < W) or seen[yy, xx] or not walk[yy, xx]:
                continue
            # Game.java:3019 -- a diagonal step needs BOTH orthogonal
            # neighbours walkable; a flood without this rule squeezes through
            # diagonal cliff seams the engine cannot and lies about reachability
            # (exactly how the first v2.44 repair attempt "confirmed" divide).
            if walk[y + dy, x] and walk[y, x + dx]:
                seen[yy, xx] = True
                dq.append((yy, xx))
    return all(s is not None and seen[_snap_nearest(walk, *s)] for s in starts[1:])


def _door_path(walk, a, b):
    """Dijkstra from `a` to `b` where entering an unwalkable cell costs 1 and
    a diagonal step additionally costs 1 per blocked corner cell (the two
    orthogonal neighbours the engine's no-corner-cut rule requires).

    Corner cost is the part a plain 0-1 BFS does not see: without it the
    "cheapest" path hugs a cliff/water edge cutting diagonals at every step,
    and the corner cells it silently assumed turn the 7-door bridge crossing
    into a 250-cell excavation. Here the search pays for its corners, so the
    path it returns is the cheapest set of cells that actually has to open.

    Returns the FULL path as an ordered list of (y, x) from `a` to `b`
    (inclusive), or None when no path exists within the map. Diagonal moves
    are still free of the strict rule (this only LOCATES the repair set);
    `reachable()` re-verifies the repaired bitmap under the game rule after.
    """
    import heapq
    H, W = walk.shape
    start = a[0] * W + a[1]
    goal = b[0] * W + b[1]
    INF = 1 << 30
    dist = np.full(H * W, INF, dtype=np.int32)
    par = np.full(H * W, -1, dtype=np.int64)
    flat = walk.reshape(-1)
    dist[start] = 0
    pq = [(0, start)]
    nbr = ((1, 0), (-1, 0), (0, 1), (0, -1),
           (1, 1), (1, -1), (-1, 1), (-1, -1))
    while pq:
        dc, cur = heapq.heappop(pq)
        if dc > dist[cur]:
            continue
        if cur == goal:
            break
        cy, cx = divmod(int(cur), W)
        for dy, dx in nbr:
            yy, xx = cy + dy, cx + dx
            if not (0 <= yy < H and 0 <= xx < W):
                continue
            ni = yy * W + xx
            c = 0 if flat[ni] else 1
            if dy != 0 and dx != 0:
                if not flat[cy * W + xx]:
                    c += 1          # corner (cy, xx) must open too
                if not flat[yy * W + cx]:
                    c += 1          # corner (yy, cx) must open too
            nd = dc + c
            if nd < dist[ni]:
                dist[ni] = nd
                par[ni] = cur
                heapq.heappush(pq, (nd, ni))
    if dist[goal] >= INF:
        return None
    path = []
    cur = goal
    while cur != -1:
        cy, cx = divmod(int(cur), W)
        path.append((cy, cx))
        if cur == start:
            break
        cur = int(par[cur])
    path.reverse()
    return path


def repair_walk(walk, starts):
    """v2.44: make the SHIPPED walk bitmap actually connect the starts.

    The v2.16 gate validated `_dilate(_fill_enclosed(walk), 1)` while the bake
    wrote the RAW bitmap, so a map whose chokepoints are single blocked
    minitiles passed the gate yet was impassable in the engine (The Small
    Divide: seven door cells across its bridges -- the AI could not cross,
    patrol orders froze, workers starved; see tools/_walkaudit.py, which is
    the audit that caught the mismatch).

    Repair is conservative and minimal:
      1. fill enclosed pockets only (_fill_enclosed) -- the sea touches the
         map border, so water is never filled and islands stay islands;
      2. if the starts are still apart, 0-1 BFS the cheapest door path and
         open exactly the blocked cells on it, then re-verify under the
         strict game rule (`reachable`); iterate a bounded number of rounds;
      3. give up (return None) when the doors exceed DOOR_CAP -- that is a
         genuine island, not damage, and the caller keeps its island verdict.
    """
    DOOR_CAP = 96
    ship = _fill_enclosed(walk).astype(bool)
    for _ in range(6):
        if reachable(ship, starts):
            return ship.astype(np.uint8)
        # connect every start to the first one, collecting doors as we go
        seeds = [_snap_nearest(ship, sx, sy) for sx, sy in starts]
        if any(s is None for s in seeds):
            return None
        doors = []
        for s in seeds[1:]:
            dp = _door_path(ship, seeds[0], s)
            if dp is None:
                return None
            # Open the blocked cells on the path AND the two corner cells of
            # every diagonal step. The strict flood refuses a diagonal whose
            # orthogonal neighbours are blocked, so opening only the path
            # cells can leave a door the engine still cannot enter while the
            # free-diagonal search believes it is through -- an empty door
            # list on the next round and a repair that gives up. The corner
            # cells sit between consecutive path cells, so on a bridge or a
            # ramp they are bridge/ramp surface, not a wall face.
            for i, (y, x) in enumerate(dp):
                if not ship[y, x]:
                    doors.append((y, x))
                if i:
                    py, px = dp[i - 1]
                    if (y != py) and (x != px):
                        for cy, cx in ((py, x), (y, px)):
                            if not ship[cy, cx]:
                                doors.append((cy, cx))
        if not doors:
            return None          # reachable() says no but no doors: give up
        if len(doors) > DOOR_CAP:
            return None          # a real island, not a damaged bridge
        for (y, x) in doors:
            ship[y, x] = True
    return None


def map_census(src):
    """One row of the v2.16 gate table: dims, start count, minerals, geysers,
    tileset, and whether the starts are connected. Returns None when the map
    cannot be read/built at all."""
    r = read_chk(os.path.join(ROOT, src))
    if not r:
        return None
    chk, gaps = r
    g, sec = parse_chk(chk, gaps)
    if b"DIM " not in sec or b"MTXM" not in sec or b"ERA " not in sec:
        return None
    off, _ = sec[b"DIM "]
    w, h = g.u16(off), g.u16(off + 2)
    if w > 256 or h > 256 or w < 32 or h < 32:
        return None
    eoff, _ = sec[b"ERA "]
    ts = load_tileset(TILESETS.get(g.byte(eoff), "platform"))
    if ts is None:
        return None
    moff, _ = sec[b"MTXM"]
    mtwm = [g.u16(moff + i * 2) for i in range(w * h)]
    walk = _walk_bitmap(w, h, mtwm, ts)
    starts = _starts_of(g, sec)
    ok, _ = connectivity(walk, starts)
    minerals = geysers = 0
    if b"UNIT" in sec:
        off, size = sec[b"UNIT"]
        for i in range(size // 36):
            uid = g.u16(off + i * 36 + 8)
            if uid in MINERAL_IDS:
                minerals += 1
            elif uid == GEYSER_ID:
                geysers += 1
    return {"id": os.path.splitext(os.path.basename(src))[0], "w": w, "h": h,
            "tileset": ts["name"], "starts": len(starts), "minerals": minerals,
            "geysers": geysers, "connected": ok}


def build_map(src, map_id, name_cn):
    r = read_chk(os.path.join(ROOT, src))
    if not r:
        return False
    chk, gaps = r
    g, sec = parse_chk(chk, gaps)
    if b"DIM " not in sec or b"MTXM" not in sec or b"ERA " not in sec:
        return False
    off, _ = sec[b"DIM "]
    w, h = g.u16(off), g.u16(off + 2)
    # SC1 maps are 64/96/128/192/256 per side; the old 128 cap silently
    # dropped (2)River Crossing, a legal 96x256 map (v2.4's missing 10th map).
    if w > 256 or h > 256 or w < 32 or h < 32:
        return False
    off, _ = sec[b"ERA "]
    ts = load_tileset(TILESETS.get(g.byte(off), "platform"))
    if ts is None:
        return False
    off, size = sec[b"MTXM"]
    mtwm = [g.u16(off + i * 2) for i in range(w * h)]

    outdir = os.path.join(OUT, "maps", map_id)
    os.makedirs(outdir, exist_ok=True)
    W, H = w * 32, h * 32
    chunks = {}
    # v2.16 batch 3.1: the walk bitmap comes from the vectorised reader (the
    # same chain as the old inline loop, verified byte-for-byte by the
    # [maps] desktop assertion), so the render loop no longer carries a second
    # copy of that math.
    walk_np = _walk_bitmap(w, h, mtwm, ts)
    # v2.23 batch C: the ground-level bitmap travels with the walk map. Same
    # dimensions (w*4 x h*4), one byte per minitile, 0/1/2 = low/mid/high.
    elev_np = _elev_bitmap(w, h, mtwm, ts)

    def chunk_at(X, Y):
        key = (X // CHUNK, Y // CHUNK)
        if key not in chunks:
            cw = min(CHUNK, W - key[0] * CHUNK)
            ch = min(CHUNK, H - key[1] * CHUNK)
            chunks[key] = Image.new("RGB", (cw, ch))
        return chunks[key]

    # v2.42 batch A: some megatiles' art is PURE black -- MTXM 0x0000 ("void",
    # outside the playable shape) resolves here, and a few custom-tileset
    # entries carry black art of their own (3kingdoms shows a handful of black
    # squares mid-map). The desktop port clamps the camera to the full map
    # rectangle, so such tiles read as black patches (divide's 3x1 run at
    # tiles (58..60, 22) was a real-device report). Pre-scan the tileset for
    # black megatiles once, then:
    #   * void tiles within Chebyshev distance 2 of real terrain render with
    #     that neighbour's megatile (isolated holes become plausible ground);
    #   * deep void keeps its black -- the original game shows the off-map sea
    #     black too, and smearing terrain across a thousand-tile sea would lie
    #     about walkability;
    #   * a per-map void mask (void.bin, 1 byte per tile) records every tile
    #     that still renders black, and the [v242] asset assertion allows pure
    #     black ONLY inside that mask.
    # Walk/elev keep reading the raw MTXM: this pass is purely cosmetic and
    # void tiles stay unwalkable wherever the art ends up.
    black_mega = set()
    for mi in range(len(ts["vx4_refs"])):
        all_black = True
        for e in ts["vx4_refs"][mi]:
            vri = e >> 1
            if vri >= len(ts["pixels"]):
                all_black = False
                break
            for v in ts["pixels"][vri]:
                if ts["pal"][v] != (0, 0, 0):
                    all_black = False
                    break
            if not all_black:
                break
        if all_black:
            black_mega.add(mi)

    def _void_of(raw):
        grp = (raw & 0x7FF0) >> 4
        var = raw & 0xF
        if grp >= len(ts["cv5_tiles"]):
            grp = 0
        vx4m = ts["cv5_tiles"][grp][var]
        if vx4m >= len(ts["vx4_refs"]):
            return True
        return vx4m in black_mega

    def _mega_at(i):
        grp = (mtwm[i] & 0x7FF0) >> 4
        var = mtwm[i] & 0xF
        if grp >= len(ts["cv5_tiles"]):
            grp = 0
        vx4m = ts["cv5_tiles"][grp][var]
        if vx4m >= len(ts["vx4_refs"]):
            vx4m = 0
        return vx4m

    void = [_void_of(raw) for raw in mtwm]
    megas = [0] * (w * h)
    for i in range(w * h):
        if not void[i]:
            megas[i] = _mega_at(i)
    void_n = sum(1 for v in void if v)
    # v2.42 batch A: only SMALL void components are bake artifacts (a handful
    # of tiles at a map seam or an authoring slip -- measured: every shipped
    # map's void is 1..6 tiles per component except six maps whose genuine
    # off-map sea runs to hundreds). A component of <= VOID_HOLE_MAX tiles is
    # filled from the nearest real terrain within Chebyshev distance 2; a
    # larger one is left black, which is exactly what the original game shows
    # for the sea around an island map. Without this split the fill smeared
    # terrain across crusader's 3000-tile sea and moved 6.6M pixels.
    VOID_HOLE_MAX = 64
    comp = [-1] * (w * h)
    sizes = []
    for i0 in range(w * h):
        if not void[i0] or comp[i0] >= 0:
            continue
        cid = len(sizes)
        stack = [i0]
        comp[i0] = cid
        n = 0
        while stack:
            i = stack.pop()
            n += 1
            x, y = i % w, i // w
            for j in (i - 1 if x > 0 else -1, i + 1 if x < w - 1 else -1,
                      i - w if y > 0 else -1, i + w if y < h - 1 else -1):
                if j >= 0 and void[j] and comp[j] < 0:
                    comp[j] = cid
                    stack.append(j)
        sizes.append(n)
    filled_n = 0
    kept_n = 0
    for ty in range(h):
        for tx in range(w):
            i = ty * w + tx
            if not void[i]:
                continue
            if sizes[comp[i]] > VOID_HOLE_MAX:
                kept_n += 1
                continue
            fill = 0
            for ry in range(max(0, ty - 2), min(h, ty + 3)):
                for rx in range(max(0, tx - 2), min(w, tx + 3)):
                    m = megas[ry * w + rx]
                    if m:
                        fill = m
                        break
                if fill:
                    break
            megas[i] = fill
            if fill:
                filled_n += 1
            else:
                kept_n += 1

    # v2.42 batch A: (vri, flip) -> 8x8 RGB tile cache. The old per-pixel
    # putpixel loop was the bake's cost centre (~2 min per 128x128 map); the
    # void sweep re-bakes 40 shipped maps, so paste a cached tile instead.
    # Output is byte-identical to the loop it replaces.
    mini_cache = {}

    def mini_tile(vri, flip):
        key = (vri << 1) | flip
        im = mini_cache.get(key)
        if im is None:
            src = ts["pixels"][vri]
            im = Image.new("RGB", (8, 8))
            ip = im.load()
            for yy in range(8):
                row = src[yy * 8:(yy + 1) * 8]
                if flip:
                    row = row[::-1]
                for xx in range(8):
                    ip[xx, yy] = ts["pal"][row[xx]]
            mini_cache[key] = im
        return im

    for ty in range(h):
        for tx in range(w):
            vx4m = megas[ty * w + tx]
            refs = ts["vx4_refs"][vx4m]
            flags = ts["vf4_flags"][vx4m] if vx4m < len(ts["vf4_flags"]) else None
            for k in range(16):
                e = refs[k]
                # VX4 u16 = VR4 id in bits 1..15, bit 0 = horizontally flipped.
                # Reading bit 15 as the flip doubles the VR4 id and walks off
                # the palette image, which is what painted the black bands.
                vri = e >> 1
                flip = e & 1
                if vri >= len(ts["pixels"]):
                    # v2.42 batch A: an out-of-range VR4 reference used to skip
                    # the minitile, leaving the chunk's black Image.new base.
                    # Clamp to the last valid tile instead -- a plausible
                    # neighbor beats a black hole, and the [v242] asset sweep
                    # asserts no >=8x8 pure-black rect survives anywhere.
                    vri = len(ts["pixels"]) - 1
                wk = 1 if (flags is not None and (flags[k] & 0x0001)) else 0
                mx = (k % 4) * 8
                my = (k // 4) * 8
                img = chunk_at(tx * 32 + mx, ty * 32 + my)
                opx = tx * 32 + mx - (tx * 32 + mx) // CHUNK * CHUNK
                opy = ty * 32 + my - (ty * 32 + my) // CHUNK * CHUNK
                img.paste(mini_tile(vri, flip), (opx, opy))

    for (cx, cy), img in chunks.items():
        img.save(os.path.join(outdir, "c_%d_%d.png" % (cx, cy)), optimize=True)

    # v2.42 batch A: the void mask, 1 byte per tile -- 1 where the FINAL
    # megatile still paints black (deep off-map sea). The [v242] asset
    # assertion reads this: pure-black pixels are legal only inside a masked
    # tile, so an accidental black hole anywhere else fails the gate.
    void_mask = bytearray(w * h)
    for i in range(w * h):
        void_mask[i] = 1 if megas[i] in black_mega else 0
    with open(os.path.join(outdir, "void.bin"), "wb") as fp:
        fp.write(bytes(void_mask))

    # minimap
    mini_img = Image.new("RGB", (w * 4, h * 4))
    mpx = mini_img.load()
    for (cx, cy), img in chunks.items():
        small = img.resize((img.width // 8, img.height // 8))
        mpx_small = small.load()
        for y in range(small.height):
            for x in range(small.width):
                mpx[cx * 64 + x, cy * 64 + y] = mpx_small[x, y]
    mini_img.save(os.path.join(outdir, "minimap.png"), optimize=True)

    # units
    units = []
    starts = []
    if b"UNIT" in sec:
        off, size = sec[b"UNIT"]
        for i in range(size // 36):
            base = off + i * 36
            uid = g.u16(base + 8)
            x = g.u16(base + 4)
            y = g.u16(base + 6)
            owner = g.u16(base + 16)
            if uid in MINERAL_IDS:
                units.append({"u": 1, "x": x, "y": y, "o": 0,
                              "v": 1500, "m": uid - 176})
            elif uid == GEYSER_ID:
                units.append({"u": 2, "x": x, "y": y, "o": 0, "v": 5000})
            elif uid == START_ID:
                starts.append([x, y])
    # v2.23 batch A: the connectivity result is recorded rather than acted on.
    # A map whose starts sit on separate landmasses is no longer dropped --
    # with transports in the game it is playable, and the picker badges it as
    # an airlift map. The gate itself is unchanged, only its consequence.
    # v2.42: connectivity indexes the walk bitmap, which is a *minitile* grid
    # (w*4 x h*4). `starts` above holds raw CHK pixels for meta.json, so it must
    # not be fed in directly: a 64x64 map's pixel x=1728 lands far outside the
    # 256-wide bitmap and `snap` finds nothing, which reported every map as an
    # island. Divide the pixels down to minitiles exactly as _starts_of does.
    starts_mini = [(sx // 8, sy // 8) for sx, sy in starts]
    # v2.44: the bitmap that ships is the bitmap A* walks, so the verdict the
    # meta carries is computed on the REPAIRED bitmap with the strict game
    # rule -- not on a relaxed reading the engine never sees. repair_walk
    # returns None for a genuine island, in which case the raw bitmap ships
    # unchanged and the island flag says so.
    walk_ship = repair_walk(walk_np, starts_mini)
    if walk_ship is None:
        walk_ship = walk_np
    connected = reachable(walk_ship, starts_mini)
    meta = {"name": name_cn, "id": map_id, "w": w, "h": h,
            "tileset": ts["name"], "starts": starts, "units": units,
            "elev": 1, "island": 0 if connected else 1}

    # DD2 / DDDATA: doodad placements. Record = {u16 type, u16 x, u16 y,
    # u8 owner, u8 state}. The id->art mapping lives in the exe-embedded
    # doodads.dat, which this repack's binaries have resisted every reverse
    # attempt so far (see v2.9方案 batch D notes) -- so we ship the
    # placements as data; the renderer draws what it can resolve and skips
    # the rest rather than guessing.
    doodads = []
    dd_key = b"DD2 " if b"DD2 " in sec else (b"DDDATA" if b"DDDATA" in sec else None)
    if dd_key:
        doff, dsize = sec[dd_key]
        for i in range(dsize // 8):
            base = doff + i * 8
            doodads.append({"t": g.u16(base), "x": g.u16(base + 2),
                            "y": g.u16(base + 4)})
    meta["doodads"] = doodads
    with open(os.path.join(outdir, "meta.json"), "w", encoding="utf8") as fp:
        json.dump(meta, fp, ensure_ascii=False)
    lines = ["name=%s" % name_cn, "w=%d" % w, "h=%d" % h, "tileset=%s" % ts["name"],
             "elev=1"]
    if not connected:
        lines.append("island=1")
    for sx, sy in starts:
        lines.append("start=%d,%d" % (sx, sy))
    for u in units:
        if u["u"] == 1:
            lines.append("unit=1,%d,%d,0,0,%d" % (u["x"], u["y"], u.get("m", 0)))
        else:
            lines.append("unit=2,%d,%d,0,0,0" % (u["x"], u["y"]))
    for dd in doodads:
        lines.append("doodad=%d,%d,%d" % (dd["t"], dd["x"], dd["y"]))
    with open(os.path.join(outdir, "meta.txt"), "w", encoding="utf8") as fp:
        fp.write("\n".join(lines))
    with open(os.path.join(outdir, "walk.bin"), "wb") as fp:
        fp.write(walk_ship.tobytes())
    with open(os.path.join(outdir, "elev.bin"), "wb") as fp:
        fp.write(elev_np.tobytes())
    print("map %-12s %dx%d ts=%-9s starts=%d units=%d chunks=%d high=%d void=%d"
          " kept=%d blackMega=%d%s" % (
        map_id, w, h, ts["name"], len(starts), len(units), len(chunks),
        int((elev_np >= 1).sum()), void_n, kept_n, len(black_mega),
        "" if connected else " ISLAND"))
    return True


# v2.16 batch 3.2: the shipped set. Every entry was put through the
# connectivity gate above before being listed; the three groups drive the
# skirmish picker's sticky headers (group column in index.txt).
#   ladder = 天梯经典     bw = BW 瓦片集展示     fun = 休闲遭遇战
MAPS = [
    # --- ladder (8)
    ("maps\\ladder\\(4)Lost Temple.scm", "losttemple", "失落神庙", "ladder"),
    ("maps\\ladder\\(4)Rivalry.scm", "rivalry", "争锋", "ladder"),
    ("maps\\ladder\\(4)Ashrigo.scm", "ashrigo", "阿什里戈", "ladder"),
    ("maps\\ladder\\(6)Acropolis.scm", "acropolis", "卫城", "ladder"),
    ("maps\\ladder\\(4)Proving Grounds.scm", "provinggrounds", "试炼场", "ladder"),
    ("maps\\oldladder\\(4)Bone Canyon.scm", "bonecanyon", "白骨峡谷", "ladder"),
    ("maps\\oldladder\\(4)Crusader.scm", "crusader", "十字军", "ladder"),
    ("maps\\oldladder\\(4)Remote Outpost.scm", "remoteoutpost", "偏远哨站", "ladder"),
    # --- bw tileset showcase (10)
    ("maps\\BroodWar\\(8)Frozen Sea.scx", "frozensea", "冰封之海", "bw"),
    ("maps\\BroodWar\\(6)Thin Ice.scx", "thinice", "薄冰", "bw"),
    ("maps\\BroodWar\\(4)Scorched Earth.scx", "scorchedearth", "焦土", "bw"),
    ("maps\\BroodWar\\(6)Sirocco.scx", "sirocco", "热风", "bw"),
    ("maps\\BroodWar\\(4)Wasteland.scx", "wasteland", "荒原", "bw"),
    ("maps\\BroodWar\\(4)Nightfall.scx", "nightfall", "夜幕", "bw"),
    ("maps\\BroodWar\\(4)Sanctuary.scx", "sanctuary", "圣所", "bw"),
    ("maps\\BroodWar\\(6)Azure Plains.scx", "azureplains", "碧蓝平原", "bw"),
    ("maps\\BroodWar\\(6)Close Encounters.scx", "closeencounters", "近距遭遇", "bw"),
    ("maps\\BroodWar\\(4)River Lethe.scx", "riverlethe", "忘川", "bw"),
    # --- fun skirmish (12)
    ("maps\\BroodWar\\(7)Broken Steppes.scm", "brokensteppes", "破碎草原", "fun"),
    ("maps\\BroodWar\\(8)Theatre of War.scm", "theatreofwar", "战争剧场", "fun"),
    ("maps\\BroodWar\\(8)Tribes.scm", "tribes", "部族", "fun"),
    ("maps\\(8)Jungle Rumble.scm", "junglerumble", "丛林混战", "fun"),
    ("maps\\(8)Killing Fields.scm", "killingfields", "杀戮战场", "fun"),
    ("maps\\(8)Plains of Snow '98.scm", "plainsofsnow", "雪原", "fun"),
    ("maps\\(8)River Runs Through It.scm", "riverruns", "大河奔流", "fun"),
    ("maps\\scenario\\(4)King of the Hill.scm", "kingofthehill", "山丘之王", "fun"),
    ("maps\\scenario\\(4)Zergling Round-Up.scm", "zerglingroundup", "围捕跳虫", "fun"),
    ("maps\\BroodWar\\WebMaps\\(8)Big Game Hunters.scm", "biggamehunters", "狩猎者", "fun"),
    ("maps\\BroodWar\\WebMaps\\(4)Crossroads.scm", "crossroads", "十字路口", "fun"),
    ("maps\\(6)New Gettysburg.scm", "newgettysburg", "新葛底斯堡", "fun"),
    # --- v2.23 batch A: the island maps the v2.16 connectivity gate used to
    # drop. With transports in the game they are playable, so they ship in a
    # fourth group and the picker badges them as airlift maps. The gate result
    # is still recorded in meta (island=1), it just no longer removes the map.
    ("maps\\(5)Island Hop.scm", "islandhop", "岛屿跳跃", "island"),
    ("maps\\BroodWar\\(6)Sapphire Isles.scx", "sapphireisles", "蓝宝石群岛", "island"),
    ("maps\\BroodWar\\(8)Primeval Isles.scx", "primevalisles", "古老群岛", "island"),
    ("maps\\BroodWar\\(4)Archipelago.scm", "archipelago", "列岛", "island"),
    ("maps\\BroodWar\\(3)Stepping Stones.scm", "steppingstones", "踏脚石", "island"),
    ("maps\\BroodWar\\(4)Kakaru Keys.scx", "kakarukeys", "卡卡鲁群岛", "island"),
    ("maps\\BroodWar\\Allied\\(6)Triple Team.scm", "tripleteam", "三人行", "island"),
    ("maps\\BroodWar\\Allied\\(8)Allied Fortress.scm", "alliedfortress", "联盟要塞", "island"),
    ("maps\\BroodWar\\Allied\\(8)Double Diamond.scm", "doublediamond", "双钻石", "island"),
    ("maps\\(2)Space Madness.scm", "spacemadness", "宇宙疯狂", "island"),
    ("maps\\BroodWar\\(6)Hypothermia.scx", "hypothermia", "低温症", "island"),
    ("maps\\(7)River War.scm", "riverwar", "河流战争", "island"),
]

# Existing shipped ids keep their group so the picker's headers are complete.
LEGACY_GROUPS = {"bloodbath": "fun", "bottleneck": "ladder", "boxer": "ladder",
                 "hunters": "fun", "darkcrystal": "fun", "river": "fun",
                 "3kingdoms": "fun", "divide": "ladder", "cyclone": "fun",
                 "volcanis": "fun"}


def add_elevation(src, map_id):
    """v2.23 batch C/A: write elev.bin and the meta flags for a shipped map
    WITHOUT re-rendering its terrain art.

    build_map() regenerates the chunk PNGs, which would both cost minutes per
    map and litter the asset tree with PNGs next to the slimmed WEBPs. This
    pass reads the same CHK, computes the same walk and high bitmaps, and only
    touches elev.bin plus the meta elev=/island= lines, so the shipped terrain
    is left byte-identical and the asset diff stays clean.
    """
    r = read_chk(os.path.join(ROOT, src))
    if not r:
        return False
    chk, gaps = r
    g, sec = parse_chk(chk, gaps)
    if b"DIM " not in sec or b"MTXM" not in sec or b"ERA " not in sec:
        return False
    off, _ = sec[b"DIM "]
    w, h = g.u16(off), g.u16(off + 2)
    if w > 256 or h > 256 or w < 32 or h < 32:
        return False
    eoff, _ = sec[b"ERA "]
    ts = load_tileset(TILESETS.get(g.byte(eoff), "platform"))
    if ts is None:
        return False
    moff, _ = sec[b"MTXM"]
    mtwm = [g.u16(moff + i * 2) for i in range(w * h)]
    walk_np = _walk_bitmap(w, h, mtwm, ts)
    elev_np = _elev_bitmap(w, h, mtwm, ts)
    starts = _starts_of(g, sec)
    connected, _ = connectivity(walk_np, starts)

    outdir = os.path.join(OUT, "maps", map_id)
    if not os.path.isdir(outdir):
        return False
    with open(os.path.join(outdir, "elev.bin"), "wb") as fp:
        fp.write(elev_np.tobytes())

    # meta.txt: rewrite with the two new flags, keeping every other line as is.
    mtxt = os.path.join(outdir, "meta.txt")
    with open(mtxt, "r", encoding="utf8") as fp:
        lines = [ln.rstrip("\n") for ln in fp.readlines()]
    out = []
    seen_elev = False
    for ln in lines:
        if ln.startswith("elev=") or ln.startswith("island="):
            continue
        out.append(ln)
        if ln.startswith("tileset=") and not seen_elev:
            out.append("elev=1")
            if not connected:
                out.append("island=1")
            seen_elev = True
    if not seen_elev:
        out.append("elev=1")
        if not connected:
            out.append("island=1")
    with open(mtxt, "w", encoding="utf8") as fp:
        fp.write("\n".join(out))

    # meta.json: same two flags, so a tool reading the JSON agrees with the txt.
    mjson = os.path.join(outdir, "meta.json")
    if os.path.exists(mjson):
        meta = json.load(open(mjson, encoding="utf8"))
        meta["elev"] = 1
        meta["island"] = 0 if connected else 1
        with open(mjson, "w", encoding="utf8") as fp:
            json.dump(meta, fp, ensure_ascii=False)

    print("elev %-16s %3dx%-3d elevated=%7d %s" % (
        map_id, w, h, int((elev_np >= 1).sum()),
        "connected" if connected else "ISLAND"))
    return True


def census_all(root=None):
    """Run the connectivity gate over every .scm/.scx on disk.

    Returns (playable, rejected): lists of census dicts. This is the step the
    plan insists on running BEFORE a human picks maps -- the 153-map pool is
    first narrowed to the maps whose start locations are all mutually
    reachable.
    """
    root = root or os.path.join(ROOT, "maps")
    files = []
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            if f.lower().endswith((".scm", ".scx")):
                files.append(os.path.join(dp, f))
    playable, rejected, unreadable = [], [], []
    for f in sorted(files):
        rel = os.path.relpath(f, ROOT)
        try:
            row = map_census(rel)
        except Exception:
            row = None
        if row is None:
            unreadable.append(rel)
        elif row["connected"]:
            playable.append(row)
        else:
            rejected.append(row)
    return playable, rejected, unreadable


if __name__ == "__main__":
    import sys
    if "--census" in sys.argv:
        playable, rejected, unreadable = census_all()
        print("playable=%d rejected=%d unreadable=%d" % (
            len(playable), len(rejected), len(unreadable)))
        print("--- rejected (islands / disconnected starts) ---")
        for r in rejected:
            print("  %-44s %3dx%-3d starts=%d" % (r["id"], r["w"], r["h"], r["starts"]))
        print("--- playable pool ---")
        for r in playable:
            print("  %-44s %3dx%-3d starts=%d m=%3d g=%2d ts=%s" % (
                r["id"], r["w"], r["h"], r["starts"], r["minerals"], r["geysers"],
                r["tileset"]))
        sys.exit(0)

    # gate first: narrow the disk pool, then build only what passed.
    playable, rejected, unreadable = census_all()
    print("connectivity gate: playable=%d rejected=%d unreadable=%d" % (
        len(playable), len(rejected), len(unreadable)))
    for r in rejected:
        print("  DROP %-40s (starts on %d separate landmasses)" % (r["id"], r["starts"]))
    ok = 0
    for src, mid, name, group in MAPS:
        if build_map(src, mid, name):
            ok += 1
    print("built %d/%d maps" % (ok, len(MAPS)))
    write_map_index()
    print("index.txt written")


def write_map_index():
    """index.txt row: id|名称|w|h|组. Group in {skirmish,ladder,bw,fun}."""
    order = {"ladder": 0, "bw": 1, "fun": 2, "island": 3, "skirmish": 4}
    rows = []
    mdir = os.path.join(OUT, "maps")
    for mid in os.listdir(mdir):
        p = os.path.join(mdir, mid, "meta.json")
        if not os.path.exists(p):
            continue
        meta = json.load(open(p, encoding="utf8"))
        group = LEGACY_GROUPS.get(mid)
        if group is None:
            for _src, m2, _n, g2 in MAPS:
                if m2 == mid:
                    group = g2
                    break
        group = group or "skirmish"
        rows.append((order.get(group, 9), meta["name"], mid, meta, group))
    # group-major order so the picker's sticky headers are contiguous
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    lines = []
    for _o, _nm, mid, meta, group in rows:
        # v2.23 batch A: a sixth column marks an airlift map. meta.json has
        # carried island= since the gate stopped dropping maps; the picker
        # only needs the flag, so it rides here rather than in a second read.
        lines.append("%s|%s|%d|%d|%s|%d" % (
            mid, meta["name"], meta["w"], meta["h"], group,
            1 if meta.get("island") else 0))
    with open(os.path.join(mdir, "index.txt"), "w", encoding="utf8") as fp:
        fp.write("\n".join(lines) + "\n")


def write_sprite_manifest():
    """Sprites manifest.txt: key,kind,walkRows,hasAttack,frames"""
    import pipeline_sprites as ps
    lines = []
    for key, spec in ps.UNITS.items():
        path, walk_blocks, attack_block, n_dir_blocks = spec
        if n_dir_blocks == 0:
            # count frames actually available
            for ar in (ps.PT, ps.SD, ps.BD):
                if ar.has(path):
                    try:
                        frames, mw, mh = grpm = __import__("grp").decode_grp(
                            *(lambda t: (t[0], t[1]))(*ar.read_with_gaps(path)))
                    except Exception:
                        continue
                    frames_n = len(frames)
                    lines.append("%s,1,0,0,%d" % (key, min(frames_n, 6)))
                    break
        else:
            lines.append("%s,0,%d,%d,0" % (key, len(walk_blocks or []), 1 if attack_block is not None else 0))
    with open(os.path.join(ps.OUT, "sprites", "manifest.txt"), "w", encoding="utf8") as fp:
        fp.write("\n".join(lines))
    print("sprite manifest written")

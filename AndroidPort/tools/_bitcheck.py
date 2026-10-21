"""v2.44: is the walkable bit really bit0 alone, or bit0|bit1?

VF4 flag word bits (BW convention):
   0x0001 walkable   0x0002 buildable/mid   0x0004 high   0x0008 blocks view   0x0010 ramp

The bake reads bit0 only (pipeline_maps.py:537).  If the game really treats
"mid ground" (bit1) as walkable too, then our shipped walk.bin.gz has been
strictly too small on every map, which would show up as exactly the symptom the
user reports: units refusing to path to places they should reach.

Judge by the twelve maps the bake itself calls islands: a reading that fuses
them into one landmass is wrong.  Also check the main maps, which must be
connected.
"""
import os
import sys
from collections import deque

import numpy as np

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

# build_maps_v223.py:10-21 -- the ten maps shipped before MAPS grew its groups
LEGACY = {
    "bloodbath": r"maps\(4)Blood Bath.scm",
    "bottleneck": r"maps\(2)Bottleneck.scm",
    "boxer": r"maps\(2)Boxer.scm",
    "hunters": r"maps\(8)The Hunters.scm",
    "darkcrystal": r"maps\(4)Dark Crystal.scm",
    "river": r"maps\(2)River Crossing.scm",
    "3kingdoms": r"maps\(3)Three Kingdoms.scm",
    "divide": r"maps\(2)The Small Divide.scm",
    "cyclone": r"maps\(4)Cyclone.scm",
    "volcanis": r"maps\(2)Volcanis.scm",
}
SRC = {m[1]: m[0] for m in pm.MAPS}
SRC.update(LEGACY)

ISLANDS = ["islandhop", "sapphireisles", "primevalisles", "archipelago",
           "steppingstones", "kakarukeys", "tripleteam", "alliedfortress",
           "doublediamond", "spacemadness", "hypothermia", "riverwar"]
MAINS = ["bottleneck", "bloodbath", "boxer", "hunters", "losttemple", "acropolis",
         "provinggrounds", "bonecanyon", "crusader", "remoteoutpost", "divide"]


def load(mid):
    chk, gaps = pm.read_chk(os.path.join(pm.ROOT, SRC[mid]))
    g, sec = pm.parse_chk(chk, gaps)
    off, _ = sec[b"DIM "]
    w, h = g.u16(off), g.u16(off + 2)
    eoff, _ = sec[b"ERA "]
    ts = pm.load_tileset(pm.TILESETS.get(g.byte(eoff), "platform"))
    moff, _ = sec[b"MTXM"]
    mt = np.array([g.u16(moff + 2 * i) for i in range(w * h)], dtype=np.uint32).reshape(h, w)
    grp = np.clip((mt & 0x7FF0) >> 4, 0, len(ts["cv5_tiles"]) - 1)
    tiles = np.asarray(ts["cv5_tiles"], dtype=np.int64)
    vx4m = tiles[grp, mt & 0xF]
    fl = np.asarray(ts["vf4_flags"], dtype=np.int64)
    vx4m = np.where(vx4m >= len(fl), 0, vx4m)
    ff = fl[vx4m].reshape(h, w, 4, 4)
    uoff, usize = sec[b"UNIT"]
    st = []
    for i in range(usize // 36):
        b = uoff + i * 36
        if g.u16(b + 8) == pm.START_ID:
            st.append((g.u16(b + 4) // 8, g.u16(b + 6) // 8))
    return ff, st


def comps(walk):
    MH, MW = walk.shape
    comp = -np.ones((MH, MW), dtype=np.int32)
    cid = 0
    for sy in range(MH):
        for sx in range(MW):
            if comp[sy, sx] != -1 or not walk[sy, sx]:
                continue
            stk = [(sx, sy)]
            comp[sy, sx] = cid
            while stk:
                x, y = stk.pop()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < MW and 0 <= ny < MH and walk[ny, nx] and comp[ny, nx] == -1:
                            comp[ny, nx] = cid
                            stk.append((nx, ny))
            cid += 1
    return comp, cid


READINGS = [
    ("bit0", lambda ff: (ff & 1) != 0),
    ("bit0|bit1", lambda ff: ((ff & 1) | ((ff >> 1) & 1)) != 0),
]


def run(mid, expect_same):
    ff, st = load(mid)
    cells = []
    for label, f in READINGS:
        m = f(ff)
        walk = m.transpose(0, 2, 1, 3).reshape(ff.shape[0] * 4, ff.shape[1] * 4)
        comp, n = comps(walk)
        if len(st) >= 2:
            same = int(comp[st[0][1], st[0][0]]) == int(comp[st[1][1], st[1][0]])
        else:
            same = None
        mark = "" if same is None else ("  " if same == expect_same else "  <<< WRONG")
        cells.append("%s comps=%-4d walk=%-6d SAME=%-5s%s"
                     % (label, n, int(walk.sum()), same, mark))
    print("   %-15s expect SAME=%-5s | %s | %s" % (mid, expect_same, cells[0], cells[1]))


print("== main maps (all must be SAME=True, except divide which the bake claims connected)")
for mid in MAINS:
    run(mid, True)
print()
print("== the twelve maps the bake calls islands (must stay SAME=False)")
for mid in ISLANDS:
    run(mid, False)

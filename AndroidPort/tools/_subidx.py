"""v2.44: is the per-tile sub-index mapping in _walk_bitmap correct?

_walk_bitmap ends with
    (f & 1).astype(uint8).transpose(0, 2, 1, 3).reshape(h*4, w*4)
where f came from f.reshape(h, w, 4, 4).  That reads the 16 sub-flags as
[row][col] and transposes them into place.  If VF4 is actually stored
column-major, every tile's 4x4 pattern is rotated -- which can seal a one or
two minitile wide passage and would explain divide.

Judge it with maps whose answer is not in doubt: the twelve maps the bake
already flags as islands must STILL be islands (multi-component) under the
correct mapping.  A mapping that fuses them into one landmass is wrong.
"""
import gzip
import os
import sys

import numpy as np

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

OUT = pm.OUT
MAPS = [
    ("divide", r"maps\(2)The Small Divide.scm"),
    ("bottleneck", r"maps\(2)Bottleneck.scm"),
    ("bloodbath", r"maps\(4)Blood Bath.scm"),
    ("islandhop", None),
    ("sapphireisles", None),
    ("primevalisles", None),
    ("steppingstones", None),
    ("kakarukeys", None),
    ("hypothermia", None),
]

# map_id -> scm path, from the pipeline's own table
SRC = {m[1]: m[0] for m in pm.MAPS}


def flags_minitile(scm):
    chk, gaps = pm.read_chk(os.path.join(pm.ROOT, scm))
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
    return fl[vx4m].reshape(h, w, 4, 4), mt


def walk_a(f):
    """current pipeline mapping: sub k = row*4 + col, transposed into place"""
    return (f & 1).astype(np.uint8).transpose(0, 2, 1, 3).reshape(f.shape[0] * 4, f.shape[1] * 4)


def walk_b(f):
    """alternative: sub k = col*4 + row (column major)"""
    return (f & 1).astype(np.uint8).reshape(f.shape[0] * 4, f.shape[1] * 4)


def comps(walk):
    MH, MW = walk.shape
    comp = -np.ones((MH, MW), dtype=np.int32)
    cid = 0
    for sy in range(MH):
        for sx in range(MW):
            if comp[sy, sx] != -1 or not walk[sy, sx]:
                continue
            st = [(sx, sy)]
            comp[sy, sx] = cid
            while st:
                x, y = st.pop()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < MW and 0 <= ny < MH and walk[ny, nx] and comp[ny, nx] == -1:
                            comp[ny, nx] = cid
                            st.append((nx, ny))
            cid += 1
    return comp, cid


def starts_of(scm):
    chk, gaps = pm.read_chk(os.path.join(pm.ROOT, scm))
    g, sec = pm.parse_chk(chk, gaps)
    uoff, usize = sec[b"UNIT"]
    out = []
    for i in range(usize // 36):
        b = uoff + i * 36
        if g.u16(b + 8) == pm.START_ID:
            out.append((g.u16(b + 4) // 8, g.u16(b + 6) // 8))
    return out


print("%-16s %-22s %-22s" % ("map", "mapping A (current)", "mapping B (col-major)"))
for mid, scm in MAPS:
    if scm is None:
        scm = SRC.get(mid)
    if scm is None:
        print("%-16s <no scm path>" % mid)
        continue
    try:
        f, mt = flags_minitile(scm)
    except Exception as e:
        print("%-16s <error %s>" % (mid, e))
        continue
    st = starts_of(scm)
    row = []
    for label, fn in (("A", walk_a), ("B", walk_b)):
        walk = fn(f)
        comp, n = comps(walk)
        if len(st) >= 2:
            a = comp[st[0][1], st[0][0]]
            b = comp[st[1][1], st[1][0]]
            same = a == b
            big = sorted(np.bincount(comp[comp >= 0].ravel()).tolist(), reverse=True)[:3]
            row.append("%s comps=%-4d SAME=%-5s top=%s" % (label, n, same, big))
        else:
            row.append("%s comps=%d" % (label, n))
    print("%-16s %-22s %-22s" % (mid, row[0], row[1]))

"""v2.44: single-minitile zoom at divide's thinnest crossing.

If the 3 blocked cells sit on a *ramp* (VF4 bit 4) whose walkability bit got
dropped by the repack, the map is really connected and the shipped bitmap is
wrong. If they sit on cliff art with no ramp, the map is genuinely divided and
the fix belongs in the mission, not the pipeline.
"""
import gzip
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
MID = "divide"
CS = 512


def load(mid):
    with gzip.open(os.path.join(ASSETS, mid, "walk.bin.gz"), "rb") as f:
        raw = f.read()
    meta = {}
    with open(os.path.join(ASSETS, mid, "meta.txt"), "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                k, v = line.split("=", 1)
                meta.setdefault(k, []).append(v)
    w, h = int(meta["w"][0]), int(meta["h"][0])
    return np.frombuffer(raw, dtype=np.uint8).reshape(h * 4, w * 4), w, h


# --- rebuild the raw flag words for this map straight from the CHK -----------
src = None
for d in (r"F:\KF\XJZB\maps\ladder", r"F:\KF\XJZB\maps", r"F:\KF\XJZB"):
    if os.path.isdir(d):
        for root, _dirs, files in os.walk(d):
            for fn in files:
                if "divide" in fn.lower():
                    src = os.path.join(root, fn)
                    break
            if src:
                break
    if src:
        break
print("source chk: %s" % src)

walk, w, h = load(MID)

flags = None
if src:
    r = pm.read_chk(src)
    if r:
        chk, gaps = r
        g, sec = pm.parse_chk(chk, gaps)
        off, _ = sec[b"DIM "]
        w2, h2 = g.u16(off), g.u16(off + 2)
        off, _ = sec[b"ERA "]
        ts = pm.load_tileset(pm.TILESETS.get(g.byte(off), "platform"))
        off, size = sec[b"MTXM"]
        mtwm = [g.u16(off + i * 2) for i in range(w2 * h2)]
        m = np.asarray(mtwm, dtype=np.uint32).reshape(h2, w2)
        grp = np.clip((m & 0x7FF0) >> 4, 0, len(ts["cv5_tiles"]) - 1)
        var = m & 0xF
        vx4m = np.asarray(ts["cv5_tiles"], dtype=np.int64)[grp, var]
        vx4m = np.where(vx4m >= len(ts["vx4_refs"]), 0, vx4m)
        fl = np.asarray(ts["vf4_flags"], dtype=np.int64)
        valid = vx4m < len(fl)
        f = np.where(valid[..., None], fl[np.clip(vx4m, 0, len(fl) - 1)], 0)
        f = f.reshape(h2, w2, 4, 4)
        flags = f.transpose(0, 2, 1, 3).reshape(h2 * 4, w2 * 4)
        print("flag words rebuilt %s" % (flags.shape,))

crossings = [(131, 109), (130, 110), (129, 111), (14, 189), (106, 158), (107, 159), (164, 216)]
print("\nblocked cell -> VF4 flag word (bit0 walk, bit1 mid, bit2 high, bit3 blocks-view, bit4 ramp)")
for (y, x) in crossings:
    fw = int(flags[y, x]) if flags is not None else -1
    nbrs = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            yy, xx = y + dy, x + dx
            if 0 <= yy < flags.shape[0] and 0 <= xx < flags.shape[1]:
                nbrs.append(int(flags[yy, xx]))
    print("  minitile(%3d,%3d) fw=0x%04X walk=%d mid=%d high=%d blkview=%d ramp=%d | walkable nbr fw=%s"
          % (x, y, fw, fw & 1, (fw >> 1) & 1, (fw >> 2) & 1, (fw >> 3) & 1, (fw >> 4) & 1,
             sorted(set("%04X" % n for n in nbrs))))

# tight art render, 1 minitile = 24 display px
def render(cx_m, cy_m, r_m, name):
    x0, y0 = max(0, (cx_m - r_m) * 8), max(0, (cy_m - r_m) * 8)
    x1, y1 = min(w * 32, (cx_m + r_m) * 8), min(h * 32, (cy_m + r_m) * 8)
    base = Image.new("RGB", (x1 - x0, y1 - y0), (0, 0, 0))
    for cy in range(y0 // CS, (y1 - 1) // CS + 1):
        for cx in range(x0 // CS, (x1 - 1) // CS + 1):
            p = os.path.join(ASSETS, MID, "c_%d_%d.webp" % (cx, cy))
            if os.path.exists(p):
                base.paste(Image.open(p).convert("RGB"), (cx * CS - x0, cy * CS - y0))
    sc = 6
    big = base.resize(((x1 - x0) * sc, (y1 - y0) * sc), Image.NEAREST)
    px = big.load()
    for my in range(y0 // 8, y1 // 8):
        for mx in range(x0 // 8, x1 // 8):
            ok = walk[my, mx]
            bx, by = (mx * 8 - x0) * sc, (my * 8 - y0) * sc
            # outline only: 2px border so the art stays visible
            for dy in range(8 * sc):
                for dx in range(8 * sc):
                    edge = dx < 2 or dy < 2 or dx >= 8 * sc - 2 or dy >= 8 * sc - 2
                    if not edge:
                        continue
                    if 0 <= bx + dx < big.size[0] and 0 <= by + dy < big.size[1]:
                        px[bx + dx, by + dy] = (0, 255, 0) if ok else (255, 0, 0)
    p = os.path.join(OUT, name)
    big.save(p, quality=90)
    print("saved %s  worldpx x %d..%d y %d..%d" % (p, x0, x1, y0, y1))


render(110, 130, 10, "_zoom_110_130.jpg")
render(158, 106, 10, "_zoom_158_106.jpg")

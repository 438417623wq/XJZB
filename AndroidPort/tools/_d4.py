"""Batch D probe 4: spatial distribution of tiles that resolve to megatile 0.

Renders bloodbath/divide with the bit-packed MTXM decode and prints an ASCII
map of the tiles whose VX4 megatile ref is 0 (black), plus the used-group
census so we can tell void regions from scattered decode noise.
"""
import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from gapio import GapReader
from PIL import Image

TILESET = {0: "badlands", 1: "platform", 2: "install", 3: "ashworld",
           4: "jungle", 5: "desert", 6: "ice", 7: "twilight"}


def load_cv5(ts):
    for ar in (pm.SD, pm.BD):
        p = "tileset\\%s.cv5" % ts
        if ar.has(p):
            d, g = ar.read_with_gaps(p)
            return GapReader(d, g or []), (len(d) + sum(s for _, s in (g or []))) // 52
    return None, 0


def main():
    for mid, src in (("bloodbath", r"maps\(4)Blood Bath.scm"),
                     ("divide", r"maps\(2)The Small Divide.scm")):
        chk, gaps = pm.read_chk(os.path.join(pm.ROOT, src))
        g, sec = pm.parse_chk(chk, gaps)
        o, _ = sec[b"DIM "]
        w, h = g.u16(o), g.u16(o + 2)
        eo, _ = sec[b"ERA "]
        ts = TILESET.get(g.byte(eo), "platform")
        cv, n = load_cv5(ts)
        T = pm.load_tileset(ts)
        cv5tiles = [[cv.u16(m * 52 + 20 + k * 2) for k in range(16)] for m in range(n)]
        mo, _ = sec[b"MTXM"]
        vals = [g.u16(mo + i * 2) for i in range(w * h)]
        img = Image.new("RGB", (w * 32, h * 32))
        px = img.load()
        black = [[False] * w for _ in range(h)]
        used = collections.Counter()
        for ty in range(h):
            for tx in range(w):
                v = vals[ty * w + tx]
                grp = (v & 0x7FF0) >> 4
                var = v & 0xF
                used[grp] += 1
                vx4m = cv5tiles[grp][var] if grp < n else 0
                if vx4m >= len(T["vx4_refs"]):
                    vx4m = 0
                if vx4m == 0:
                    black[ty][tx] = True
                refs = T["vx4_refs"][vx4m]
                for k in range(16):
                    e = refs[k]; vri = e & 0x7FFF; flip = (e >> 15) & 1
                    if vri >= len(T["pixels"]):
                        continue
                    mini = T["pixels"][vri]
                    mx, my = (k % 4) * 8, (k // 4) * 8
                    for yy in range(8):
                        for xx in range(8):
                            c = mini[yy * 8 + ((7 - xx) if flip else xx)]
                            px[tx * 32 + mx + xx, ty * 32 + my + yy] = T["pal"][c]
        img.save("_d4_%s.png" % mid)
        nb = sum(1 for r in black for b in r if b)
        xs = [tx for ty in range(h) for tx in range(w) if black[ty][tx]]
        ys = [ty for ty in range(h) for tx in range(w) if black[ty][tx]]
        print("== %s %dx%d ts=%s black=%d bbox x %s..%s y %s..%s" % (
            mid, w, h, ts, nb,
            min(xs) if xs else "-", max(xs) if xs else "-",
            min(ys) if ys else "-", max(ys) if ys else "-"))
        print("   vx4_refs[0] =", T["vx4_refs"][0])
        top = used.most_common(8)
        for grp, cnt in top:
            print("   grp %4d used %4d type=%d flags=0x%04X tiles=%s" % (
                grp, cnt, cv.u16(grp * 52), cv.u16(grp * 52 + 2),
                cv5tiles[grp][:6]))
        step = max(1, w // 48)
        print("   black map (x=black, .=tile):")
        for ty in range(0, h, step):
            print("     " + "".join(
                "#" if any(black[ty][tx] for tx in range(tx0, min(tx0 + step, w))) else "."
                for tx0 in range(0, w, step)))


main()

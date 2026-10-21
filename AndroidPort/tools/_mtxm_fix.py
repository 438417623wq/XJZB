import os, sys
sys.path.insert(0, ".")
import pipeline_maps as pm
from PIL import Image

def render(ts, w, h, vals, mode):
    T = pm.load_tileset(ts)
    img = Image.new("RGB", (w*32, h*32))
    px = img.load()
    n = len(T["mega_vx4"])
    blacks = 0
    for ty in range(h):
        for tx in range(w):
            v = vals[ty*w+tx]
            if mode == "old":
                cv5i = v if v < n else 0
                vx4m = T["mega_vx4"][cv5i]
            else:
                g = (v >> 4) & 0x7FF
                var = v & 0xF
                cv5i = g if g < n else 0
                vx4m = T["cv5_tiles"][cv5i][var]
            if vx4m >= len(T["vx4_refs"]):
                vx4m = 0
            if vx4m == 0:
                blacks += 1
            refs = T["vx4_refs"][vx4m]
            for k in range(16):
                e = refs[k]; vri = e & 0x7FFF; flip = (e>>15)&1
                if vri >= len(T["pixels"]): continue
                mini = T["pixels"][vri]
                mx, my = (k%4)*8, (k//4)*8
                for yy in range(8):
                    for xx in range(8):
                        c = mini[yy*8 + ((7-xx) if flip else xx)]
                        px[tx*32+mx+xx, ty*32+my+yy] = T["pal"][c]
    return img, blacks

# add cv5_tiles table to the tileset cache
import sc_archive
from gapio import GapReader
_orig = pm.load_tileset
def patched(ts):
    T = _orig(ts)
    if T is None or "cv5_tiles" in T:
        return T
    for ar in (pm.SD, pm.BD):
        p = "tileset\\%s.cv5" % ts
        if ar.has(p):
            d, g = ar.read_with_gaps(p)
            cv = GapReader(d, g or [])
            break
    nm = (len(d) + sum(s for _, s in (g or []))) // 52
    T["cv5_tiles"] = [[cv.u16(m*52 + 20 + k*2) for k in range(16)] for m in range(nm)]
    T["cv5_n"] = nm
    return T
pm.load_tileset = patched

for mid, src, ts in (("bloodbath", r"maps\(4)Blood Bath.scm", "platform"),
                     ("divide", r"maps\(2)The Small Divide.scm", "jungle")):
    chk, gaps = pm.read_chk(os.path.join(pm.ROOT, src))
    g, sec = pm.parse_chk(chk, gaps)
    o, _ = sec[b"DIM "]
    w, h = g.u16(o), g.u16(o+2)
    mo, _ = sec[b"MTXM"]
    vals = [g.u16(mo+i*2) for i in range(w*h)]
    for mode in ("old", "new"):
        img, bl = render(ts, w, h, vals, mode)
        img.save("_cmp_%s_%s.png" % (mid, mode))
        print("%-10s %-4s black tiles=%d" % (mid, mode, bl))

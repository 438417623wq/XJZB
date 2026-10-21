import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from gapio import GapReader
from PIL import Image

def cv5_of(ts):
    for ar in (pm.SD, pm.BD):
        p = "tileset\\%s.cv5" % ts
        if ar.has(p):
            d, g = ar.read_with_gaps(p)
            return GapReader(d, g or []), (len(d) + sum(s for _, s in (g or []))) // 52

def render(ts, w, h, vals, decode):
    T = pm.load_tileset(ts)
    img = Image.new("RGB", (w*32, h*32))
    px = img.load()
    blacks = 0
    for ty in range(h):
        for tx in range(w):
            cv5i = decode(vals[ty*w+tx])
            if cv5i >= len(T["mega_vx4"]): cv5i = 0
            vx4m = T["mega_vx4"][cv5i]
            if vx4m >= len(T["vx4_refs"]): vx4m = 0
            if vx4m == 0: blacks += 1
            refs = T["vx4_refs"][vx4m]
            for k in range(16):
                e = refs[k]; vri = e & 0x7FFF; flip = (e>>15)&1
                if vri >= len(T["pixels"]): continue
                mini = T["pixels"][vri]
                mx, my = (k%4)*8, (k//4)*8
                for yy in range(8):
                    for xx in range(8):
                        v = mini[yy*8 + ((7-xx) if flip else xx)]
                        px[tx*32+mx+xx, ty*32+my+yy] = T["pal"][v]
    return img, blacks

for mid, src, ts in (("bloodbath", r"maps\(4)Blood Bath.scm", "platform"),
                     ("divide", r"maps\(2)The Small Divide.scm", "jungle")):
    r = pm.read_chk(os.path.join(pm.ROOT, src))
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    o, _ = sec[b"DIM "]
    w, h = g.u16(o), g.u16(o+2)
    mo, _ = sec[b"MTXM"]
    vals = [g.u16(mo+i*2) for i in range(w*h)]
    a, ba = render(ts, w, h, vals, lambda v: v)
    b, bb = render(ts, w, h, vals, lambda v: (v & 0x7FF0) >> 4)
    a.save("_terr_%s_raw.png" % mid); b.save("_terr_%s_fix.png" % mid)
    print("%-10s tiles=%d  black(raw)=%d  black(fixed)=%d" % (mid, w*h, ba, bb))

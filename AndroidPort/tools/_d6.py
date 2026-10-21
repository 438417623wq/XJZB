"""Batch D probe 6: VX4 flip/id bit layout — pipeline (bit15=flip, id=e&0x7FFF)
vs wiki (bit0=flip, id=e>>1). Renders bloodbath both ways and reports VR4
coverage, so we can pick the layout that actually matches the archive.
"""
import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
from gapio import GapReader
from PIL import Image

TILESET = {0: "badlands", 1: "platform", 2: "install", 3: "ashworld",
           4: "jungle", 5: "desert", 6: "ice", 7: "twilight"}


def rd(ts, ext):
    for ar in (pm.SD, pm.BD):
        p = "tileset\\%s.%s" % (ts, ext)
        if ar.has(p):
            return ar.read_with_gaps(p)
    return None, None


def build(ts):
    d, g = rd(ts, "cv5")
    cv = GapReader(d, g or [])
    n = (len(d) + sum(s for _, s in (g or []))) // 52
    cv5tiles = [[cv.u16(m * 52 + 20 + k * 2) for k in range(16)] for m in range(n)]
    d, g = rd(ts, "vx4")
    vx = GapReader(d, g or [])
    nv = (len(d) + sum(s for _, s in (g or []))) // 32
    vx4 = [[vx.u16(m * 32 + k * 2) for k in range(16)] for m in range(nv)]
    d, g = rd(ts, "vr4")
    vr = GapReader(d, g or [])
    npix = (len(d) + sum(s for _, s in (g or []))) // 64
    pix = [vr.bytes_at(m * 64, 64) for m in range(npix)]
    d, g = rd(ts, "vf4")
    vf = GapReader(d, g or [])
    nf = (len(d) + sum(s for _, s in (g or []))) // 4
    walk = bytearray(npix)
    for m in range(min(nf, npix)):
        walk[m] = 1 if (vf.u32(m * 4) & 1) else 0
    T = pm.load_tileset(ts)
    return T, cv5tiles, n, vx4, nv, pix, walk


def render(T, cv5tiles, n, vx4, pix, w, h, vals, layout):
    img = Image.new("RGB", (w * 32, h * 32))
    px = img.load()
    seen = collections.Counter()
    for ty in range(h):
        for tx in range(w):
            v = vals[ty * w + tx]
            grp = (v & 0x7FF0) >> 4
            var = v & 0xF
            vx4m = cv5tiles[grp][var] if grp < n else 0
            if vx4m >= len(vx4):
                vx4m = 0
            for k in range(16):
                e = vx4[vx4m][k]
                if layout == "pipeline":
                    vri = e & 0x7FFF
                    flip = (e >> 15) & 1
                else:
                    vri = e >> 1
                    flip = e & 1
                seen[vri] += 1
                if vri >= len(pix):
                    continue
                mini = pix[vri]
                mx, my = (k % 4) * 8, (k // 4) * 8
                for yy in range(8):
                    for xx in range(8):
                        c = mini[yy * 8 + ((7 - xx) if flip else xx)]
                        px[tx * 32 + mx + xx, ty * 32 + my + yy] = T["pal"][c]
    return img, seen


def main():
    for mid, src in (("bloodbath", r"maps\(4)Blood Bath.scm"),
                     ("divide", r"maps\(2)The Small Divide.scm")):
        chk, gaps = pm.read_chk(os.path.join(pm.ROOT, src))
        g, sec = pm.parse_chk(chk, gaps)
        o, _ = sec[b"DIM "]
        w, h = g.u16(o), g.u16(o + 2)
        eo, _ = sec[b"ERA "]
        ts = TILESET.get(g.byte(eo), "platform")
        T, cv5tiles, n, vx4, nv, pix, walk = build(ts)
        mo, _ = sec[b"MTXM"]
        vals = [g.u16(mo + i * 2) for i in range(w * h)]
        print("== %s ts=%s cv5=%d vx4=%d vr4=%d" % (mid, ts, n, nv, len(pix)))
        for layout in ("pipeline", "wiki"):
            img, seen = render(T, cv5tiles, n, vx4, pix, w, h, vals, layout)
            img.save("_d6_%s_%s.png" % (mid, layout))
            used = len(seen)
            oob = sum(1 for v, c in seen.items() if v >= len(pix))
            print("   %-8s distinct vri=%d  oob=%d  max=%d  coverage=%.1f%%" % (
                layout, used, oob, max(seen), 100.0 * used / len(pix)))


main()

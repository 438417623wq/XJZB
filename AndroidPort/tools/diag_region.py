"""Render a map region under chain variants (a)/(c)/(d) for comparison."""
import os
from PIL import Image
import sc_archive
from gapio import GapReader
from pipeline_maps import read_chk, parse_chk, build_tileset, TILESETS

ROOT = r"F:\KF\XJZB"
chk, gaps = read_chk(os.path.join(ROOT, "maps\\(4)Blood Bath.scm"))
g, sec = parse_chk(chk, gaps)
off, _ = sec[b"DIM "]
w, h = g.u16(off), g.u16(off + 2)
off, _ = sec[b"ERA "]
ts = build_tileset(TILESETS.get(g.byte(off)))
off, size = sec[b"MTXM"]
mtwm = [g.u16(off + i * 2) for i in range(w * h)]
pal = ts["pal"]
W, H = w * 32, h * 32


def render(chain):
    img = Image.new("RGB", (W, H))
    px = img.load()
    for ty in range(h):
        for tx in range(w):
            cv5i = mtwm[ty * w + tx]
            if cv5i >= len(ts["megas"]):
                cv5i = 0
            for k in range(16):
                if chain == "a":
                    e = ts["vx4"][ts["megas"][cv5i][k]]
                    vri, flip = e & 0x7FFF, (e >> 15) & 1
                elif chain == "c":
                    base = ts["megas"][cv5i][0]
                    e = ts["vx4"][base + k]
                    vri, flip = e & 0x7FFF, (e >> 15) & 1
                elif chain == "d":
                    base = ts["megas"][cv5i][0]
                    vri, flip = (base * 16 + k) & 0x7FFF, 0
                if vri >= len(ts["pixels"]):
                    continue
                mini = ts["pixels"][vri]
                mx = (k % 4) * 8
                my = (k // 4) * 8
                for yy in range(8):
                    for xx in range(8):
                        v = mini[yy * 8 + ((7 - xx) if flip else xx)]
                        X, Y = tx * 32 + mx + xx, ty * 32 + my + yy
                        if 0 <= X < W and 0 <= Y < H:
                            px[X, Y] = pal[v]
    return img.crop((512, 512, 912, 712))


for chain in ("a", "c", "d"):
    render(chain).save(r"F:\KF\XJZB\AndroidPort\tools\out\region_%s.png" % chain)
    print("done", chain)

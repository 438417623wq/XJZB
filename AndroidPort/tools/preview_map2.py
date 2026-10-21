"""Render a map preview via MTXM -> CV5 -> VX4 -> VR4, with unit dots."""
import os
from PIL import Image, ImageDraw
import sc_archive
from pipeline_maps import read_chk, parse_chk, build_tileset, TILESETS, MINERAL_IDS, GEYSER_ID, START_ID

ROOT = r"F:\KF\XJZB"


def preview(src, out_png, walk_overlay=False):
    chk, gaps = read_chk(os.path.join(ROOT, src))
    g, sec = parse_chk(chk, gaps)
    off, _ = sec[b"DIM "]
    w = g.u16(off)
    h = g.u16(off + 2)
    off, _ = sec[b"ERA "]
    ts = build_tileset(TILESETS.get(g.byte(off)))
    off, size = sec[b"MTXM"]
    mtwm = [g.u16(off + i * 2) for i in range(w * h)]

    pal = ts["pal"]
    W, H = w * 32, h * 32
    img = Image.new("RGB", (W, H))
    px = img.load()
    walk = bytearray(W * H // 64)

    def draw_tile(tx, ty, cv5i):
        if cv5i >= len(ts["megas"]):
            cv5i = 0
        for k in range(16):
            vx4e = ts["vx4"][ts["megas"][cv5i][k]]
            vri = vx4e & 0x7FFF
            flip = (vx4e >> 15) & 1
            if vri >= len(ts["pixels"]):
                continue
            mini = ts["pixels"][vri]
            mx = (k % 4) * 8
            my = (k // 4) * 8
            f = ts["flags"][vri] if vri < len(ts["flags"]) else 0
            walkable = 1 if (f & 0x00E00000) == 0 else 0
            for yy in range(8):
                for xx in range(8):
                    sx = (7 - xx) if flip else xx
                    v = mini[yy * 8 + sx]
                    X = tx * 32 + mx + xx
                    Y = ty * 32 + my + yy
                    if 0 <= X < W and 0 <= Y < H:
                        px[X, Y] = pal[v]
                        walk[(Y // 8) * (W // 8) + (X // 8)] = walkable

    for ty in range(h):
        for tx in range(w):
            draw_tile(tx, ty, mtwm[ty * w + tx])

    if walk_overlay:
        dr0 = ImageDraw.Draw(img)
        for i, f in enumerate(walk):
            if f & 0x10:  # candidate walkable bit
                dr0.point((i % (W // 8)) * 8, (i // (W // 8)) * 8, fill=(0, 255, 0))

    dr = ImageDraw.Draw(img)
    off, size = sec[b"UNIT"]
    n = size // 36
    for i in range(n):
        base = off + i * 36
        uid = g.u16(base + 8)
        x = g.u16(base + 4)
        y = g.u16(base + 6)
        owner = g.u16(base + 16)
        cx, cy = x, y
        col = (255, 255, 0)
        r = 4
        if uid in MINERAL_IDS:
            col = (0, 255, 255)
        elif uid == GEYSER_ID:
            col = (0, 255, 0)
        elif uid == START_ID:
            col = (255, 0, 255)
            r = 8
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=2)

    if W > 1400:
        img = img.resize((W // 2, H // 2))
    img.save(out_png)
    print("OK", out_png, img.size)


preview("maps\\(4)Blood Bath.scm", r"F:\KF\XJZB\AndroidPort\tools\out\prev_bloodbath2.png")

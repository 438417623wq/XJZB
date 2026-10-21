"""Render a map preview: terrain + unit dots, to validate the UNIT layout."""
import os
import sys
from PIL import Image, ImageDraw
import sc_archive
from pipeline_maps import read_chk, parse_chk, build_tileset, TILESETS, MINERAL_IDS, GEYSER_ID, START_ID

ROOT = r"F:\KF\XJZB"


def preview(src, out_png):
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
    img = Image.new("RGB", (w * 32, h * 32))
    img = img.resize((w * 8, h * 8)) if w > 96 else img
    if img.width != w * 32:
        img = Image.new("RGB", (w * 32, h * 32))
    px = img.load()
    for ty in range(h):
        for tx in range(w):
            mi = mtwm[ty * w + tx] & 0x7FFF
            if mi >= len(ts["megas"]):
                continue
            for k in range(16):
                idx, flip = ts["megas"][mi][k]
                if idx >= len(ts["minis"]):
                    continue
                mini = ts["minis"][idx]
                mx = (k % 4) * 8
                my = (k // 4) * 8
                for yy in range(8):
                    for xx in range(8):
                        v = mini[yy * 8 + (7 - xx if flip else xx)]
                        px[tx * 32 + mx + xx, ty * 32 + my + yy] = pal[v]

    dr = ImageDraw.Draw(img)
    off, size = sec[b"UNIT"]
    n = size // 36
    sc = 1 if img.width == w * 32 else 0.25
    for i in range(n):
        base = off + i * 36
        uid = g.u16(base + 8)
        x = g.u16(base + 4)
        y = g.u16(base + 6)
        owner = g.u16(base + 16)
        cx, cy = int(x * sc), int(y * sc)
        col = (255, 255, 0)
        r = 3
        if uid in MINERAL_IDS:
            col = (0, 255, 255)
        elif uid == GEYSER_ID:
            col = (0, 255, 0)
        elif uid == START_ID:
            col = (255, 0, 255)
            r = 5
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=2)
        if sc == 1:
            dr.text((cx + 3, cy - 5), "%d" % owner, fill=(255, 255, 255))
    img.save(out_png)
    print("OK", out_png, img.size)


preview("maps\\(4)Blood Bath.scm", r"F:\KF\XJZB\AndroidPort\tools\out\prev_bloodbath.png")

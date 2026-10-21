"""Render the same frames with two row-base variants for visual comparison."""
import os
from PIL import Image
import sc_archive

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
wpe = SD.read("tileset\\jungle.wpe")
pal = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"


def decode_frame(d, base, shift, run_adj):
    xoff, yoff, w, h = d[base], d[base + 1], d[base + 2], d[base + 3]
    off = int.from_bytes(d[base + 4:base + 8], "little")
    lo = [int.from_bytes(d[off + i * 2:off + i * 2 + 2], "little") for i in range(h)]
    px = bytearray([255]) * (w * h)
    for row in range(h):
        p = off + lo[row] + shift
        x = 0
        while x < w and p < len(d):
            b = d[p]
            p += 1
            if b & 0x80:
                x += b & 0x7F
            elif b & 0x40:
                cnt = (b & 0x3F) + run_adj
                if p >= len(d):
                    break
                c = d[p]
                p += 1
                for k in range(cnt):
                    if x + k < w:
                        px[row * w + x + k] = c
                x += cnt
            else:
                cnt = b
                if cnt == 0:
                    continue
                for k in range(cnt):
                    if p + k < len(d) and x + k < w:
                        px[row * w + x + k] = d[p + k]
                p += cnt
                x += cnt
    return xoff, yoff, w, h, px


def sheet(name, frames, out_png, shift, run_adj):
    d = SD.read(name)
    fc = int.from_bytes(d[0:2], "little")
    mw = int.from_bytes(d[2:4], "little")
    mh = int.from_bytes(d[4:6], "little")
    cols = min(len(frames), 9)
    rows = (len(frames) + cols - 1) // cols
    img = Image.new("RGB", (cols * mw, rows * mh), (40, 40, 48))
    for k, fi in enumerate(frames):
        if fi >= fc:
            continue
        x, y, w, h, px = decode_frame(d, 6 + fi * 8, shift, run_adj)
        ox = (k % cols) * mw
        oy = (k // cols) * mh
        for yy in range(h):
            for xx in range(w):
                v = px[yy * w + xx]
                if v != 255:
                    img.putpixel((ox + x + xx, oy + y + yy), pal[v])
    img.save(out_png)
    print("OK", out_png)


for tag, shift, ra in (("A_shift0_run0", 0, 0), ("B_shift-2_run1", -2, 1)):
    sheet("unit\\terran\\marine.grp", list(range(17)), OUT + "\\marine_%s.png" % tag, shift, ra)
    sheet("unit\\terran\\control.grp", [0, 2, 4], OUT + "\\control_%s.png" % tag, shift, ra)

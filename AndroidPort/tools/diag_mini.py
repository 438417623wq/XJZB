import os
from PIL import Image
import sc_archive
from gapio import GapReader

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
if len(wpe) < 1024:
    wpe += bytes(1024 - len(wpe))
pal = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]
vx4, g2 = SD.read_with_gaps("tileset\\jungle.vx4")
vr4, g3 = SD.read_with_gaps("tileset\\jungle.vr4")
gv = GapReader(vx4, g2 or [])
gr = GapReader(vr4, g3 or [])


def minitile_pixels(idx, order, hi_first):
    px = bytearray(64)
    for b in range(32):
        byte = gr.byte(idx * 32 + b)
        a = (byte >> 4) & 0xF if hi_first else byte & 0xF
        c = byte & 0xF if hi_first else (byte >> 4) & 0xF
        if order == "row":
            px[b * 2] = a
            px[b * 2 + 1] = c
        else:
            col = b // 4
            row = (b % 4) * 2
            px[row * 8 + col] = a
            px[(row + 1) * 8 + col] = c
    return px


img = Image.new("RGB", (8 * 32, 4 * 32), (0, 0, 0))
combos = [("row", False), ("row", True), ("col", False), ("col", True)]
MEGAS = [64, 68, 80, 84, 100, 120, 200, 300]
for vi, (order, hi) in enumerate(combos):
    for t, mi in enumerate(MEGAS):
        v = gv.u16(mi * 32)
        idx = v & 0x7FFF
        px = minitile_pixels(idx, order, hi)
        for yy in range(8):
            for xx in range(8):
                img.putpixel((t * 32 + xx, vi * 32 + yy), pal[px[yy * 8 + xx]])
img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
img.save(r"F:\KF\XJZB\AndroidPort\tools\out\mini_variants.png")
print("rows top->bottom: row/lo, row/hi, col/lo, col/hi")

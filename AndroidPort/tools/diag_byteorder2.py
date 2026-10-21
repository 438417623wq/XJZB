"""Settle WPE byte order by rendering the SAME terrain chunk both ways.

Also renders the muzzle flash and a marine under each order. Whichever order
makes the flash fire-coloured while keeping terrain natural is the right one.
"""
import os
from PIL import Image, ImageDraw
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
if len(wpe) < 1024:
    wpe += bytes(1024 - len(wpe))

ORDER_BGR = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]
ORDER_RGB = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]

# --- terrain: re-render chunk 0_0 from VR4 data under each order
cv5, _ = SD.read_with_gaps("tileset\\jungle.cv5")
vx4, _ = SD.read_with_gaps("tileset\\jungle.vx4")
vr4, _ = SD.read_with_gaps("tileset\\jungle.vr4")


def terrain_swatch(pal):
    """First 32x32 world pixels = tile (0,0) from the megatile chain."""
    img = Image.new("RGB", (128, 128))
    px = img.load()
    mega = cv5[0] | (cv5[1] << 8)
    base = mega * 32
    for k in range(16):
        ref = vx4[base + k * 2] | (vx4[base + k * 2 + 1] << 8)
        vri = ref & 0x7FFF
        flip = (ref >> 15) & 1
        off = vri * 64
        mx, my = (k % 4) * 8, (k // 4) * 8
        for yy in range(8):
            for xx in range(8):
                v = vr4[off + yy * 8 + ((7 - xx) if flip else xx)]
                px[mx + xx, my + yy] = pal[v]
    return img


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def frame_img(f, pal):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    p = im.load()
    for y in range(f["h"]):
        for x in range(f["w"]):
            o = y * f["w"] + x
            if o < len(f["px"]) and f["px"][o] != 255:
                p[x, y] = pal[f["px"][o]] + (255,)
    return im


flsh = load(r"unit\thingy\tmeFlshS.grp")
bang = load(r"unit\thingy\tBangL.grp")
marine = load(r"unit\terran\marine.grp")

panels = []
for nm, pal in (("BGR (current)", ORDER_BGR), ("RGB (swapped)", ORDER_RGB)):
    terr = terrain_swatch(pal)
    ff = max(flsh[0], key=lambda f: sum(1 for v in f["px"] if v != 255))
    bf = bang[0][len(bang[0]) // 2]
    mf = marine[0][0]
    panels.append((nm, terr, frame_img(ff, pal), frame_img(bf, pal), frame_img(mf, pal)))

sc = 2
H = sum(128 * sc + 24 for _ in panels) + 8
W = 128 * sc + 8 + max(im.width * sc + 6 for _, _, _, _, im in panels) + 400
canvas = Image.new("RGB", (W, H), (26, 28, 36))
d = ImageDraw.Draw(canvas)
y = 4
for nm, terr, fl, bg, mr in panels:
    d.text((4, y), nm + "   [terrain | flash | bang | marine]", fill=(120, 255, 140))
    y += 18
    canvas.paste(terr.resize((256, 256), Image.NEAREST), (4, y))
    x = 4 + 256 + 8
    for im in (fl, bg, mr):
        big = im.resize((im.width * sc, im.height * sc), Image.NEAREST)
        canvas.paste(big, (x, y), big)
        x += big.width + 6
    y += 256 + 6
canvas.save(os.path.join(OUT, "byteorder_terrain.png"))
print("wrote byteorder_terrain.png", canvas.size)

# also compare against the SHIPPED chunk, which was made with BGR
try:
    shipped = Image.open(os.path.join(ASSETS, "maps", "volcanis", "c_0_0.png")).convert("RGB")
    ref = terrain_swatch(ORDER_BGR)
    print("shipped volcanis c_0_0 size", shipped.size, "swatch size", ref.size)
    cmp = Image.new("RGB", (shipped.width + ref.width + 12, max(shipped.height, ref.height) + 20), (26, 28, 36))
    dc = ImageDraw.Draw(cmp)
    dc.text((4, 2), "shipped (BGR)", fill=(120, 255, 140))
    dc.text((shipped.width + 12, 2), "re-render BGR", fill=(120, 255, 140))
    cmp.paste(shipped, (4, 18))
    cmp.paste(ref, (shipped.width + 12, 18))
    cmp.save(os.path.join(OUT, "chunk_compare.png"))
    print("wrote chunk_compare.png")
except Exception as e:
    print("shipped compare skipped:", e)

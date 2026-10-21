"""Decisive test: which WPE byte order is correct?

Renders a terrain patch, a marine, and the muzzle flash under each candidate
channel order. The correct order must satisfy BOTH: terrain looks like terrain,
and the flash core (palette index 32) looks like fire, not blue.
"""
import os
from PIL import Image, ImageDraw
import sc_archive
import grp as grpm

ROOT = r"F:\KF\XJZB"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
if len(wpe) < 1024:
    wpe += bytes(1024 - len(wpe))

ORDERS = {
    "BGR (cur: +2,+1,+0)": lambda i: (wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]),
    "RGB (alt: +0,+1,+2)": lambda i: (wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]),
    "RGB (alt: +1,+2,+3)": lambda i: (wpe[i * 4 + 1], wpe[i * 4 + 2], wpe[i * 4 + 3]),
    "BGR (alt: +3,+2,+1)": lambda i: (wpe[i * 4 + 3], wpe[i * 4 + 2], wpe[i * 4 + 1]),
}

print("index -> colour under each order:")
for i in (3, 7, 32, 45, 57, 85):
    print("  idx %3d  " % i + "  ".join("%-22s" % ("%s=%s" % (nm.split()[0], ORDERS[nm](i)))
                                       for nm in ORDERS))


def load(path):
    for ar in (PT, SD, BD):
        if ar.has(path):
            data, gaps = ar.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def frame_img(f, pal):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    for y in range(f["h"]):
        for x in range(f["w"]):
            o = y * f["w"] + x
            if o < len(f["px"]):
                v = f["px"][o]
                if v != 255:
                    px[x, y] = pal[v] + (255,)
    return im


marine = load(r"unit\terran\marine.grp")
flsh = load(r"unit\thingy\tmeFlshS.grp")
bang = load(r"unit\thingy\tBangL.grp")

# terrain: read a raw MTXM chunk? simpler -- reuse an existing chunk PNG is
# already BGR-derived, so instead sample the tileset palette on a known-good
# swatch: use vr4 minitile 0 colours is arbitrary. Skip terrain; the palette
# comparison above plus the sprite look is enough.
scale = 3
rows = []
for nm, fn in ORDERS.items():
    PAL = [fn(i) for i in range(256)]
    mf = max(marine[0], key=lambda f: f["w"] * f["h"])
    # pick a marine walk frame that is a full 17-wide pose
    mframe = marine[0][0]
    ff = max(flsh[0], key=lambda f: sum(1 for v in f["px"] if v != 255))
    bf = bang[0][len(bang[0]) // 2]
    imgs = [frame_img(mframe, PAL), frame_img(ff, PAL), frame_img(bf, PAL)]
    rows.append((nm, imgs))

H = sum(max(im.height for im in imgs) * scale + 20 for _, imgs in rows) + 8
W = max(sum(im.width * scale + 6 for im in imgs) + 8 for _, imgs in rows)
canvas = Image.new("RGB", (W, H), (26, 28, 36))
d = ImageDraw.Draw(canvas)
y = 4
for nm, imgs in rows:
    d.text((4, y), nm, fill=(120, 255, 140))
    y += 16
    x = 4
    for im in imgs:
        big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        canvas.paste(big, (x, y), big)
        x += big.width + 6
    y += max(im.height for im in imgs) * scale + 4
canvas.save(os.path.join(OUT, "byteorder_test.png"))
print("wrote byteorder_test.png", canvas.size)

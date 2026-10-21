"""Test team-color hypothesis: replace palette indices 8-15 with team ramps."""
import os
from PIL import Image
import sc_archive
import grp as grpm

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
base_pal = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"


def ramp(rgb_dark, rgb_bright, n=8):
    out = []
    for k in range(n):
        t = k / (n - 1)
        out.append((int(rgb_dark[0] + (rgb_bright[0] - rgb_dark[0]) * t),
                    int(rgb_dark[1] + (rgb_bright[1] - rgb_dark[1]) * t),
                    int(rgb_dark[2] + (rgb_bright[2] - rgb_dark[2]) * t)))
    return out


BLUE = ramp((16, 28, 96), (112, 168, 255))
RED = ramp((96, 12, 12), (255, 128, 96))
TEAL = ramp((8, 64, 64), (96, 224, 224))


def variant(pal):
    p = list(base_pal)
    for i in range(8):
        p[8 + i] = pal[i]
    return p


data, gaps = SD.read_with_gaps("unit\\terran\\marine.grp")
frames, mw, mh = grpm.decode_grp(data, gaps)
cols = 17
img = Image.new("RGB", (cols * (mw + 1), 3 * (mh + 4)), (25, 25, 32))
for r, pal_v in enumerate([variant(BLUE), variant(RED), base_pal]):
    for d in range(17):
        f = frames[d]
        ox = d * (mw + 1)
        oy = r * (mh + 4)
        for y in range(f["h"]):
            for x in range(f["w"]):
                v = f["px"][y * f["w"] + x]
                if v != 255:
                    img.putpixel((ox + f["x"] + x, oy + f["y"] + y), pal_v[v])
img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
img.save(OUT + "\\teamcolor_test.png")
print("OK ->", OUT + "\\teamcolor_test.png  (rows: blue, red, neutral)")

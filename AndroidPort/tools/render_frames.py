"""Render ALL frames of a GRP in a grid with frame indices, to derive the layout."""
import sys
import os
from PIL import Image, ImageDraw
import sc_archive
import grp as grpm

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
BD = sc_archive.Archive(r"F:\KF\XJZB\BrooDat.mpq")
wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
pal = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"


def render(name, out_png):
    for ar in (SD, BD):
        if ar.has(name):
            data, gaps = ar.read_with_gaps(name)
            break
    else:
        print("MISS", name)
        return
    frames, mw, mh = grpm.decode_grp(data, gaps)
    n = len(frames)
    cols = 17
    rows = (n + cols - 1) // cols
    img = Image.new("RGB", (cols * (mw + 1), rows * (mh + 9)), (25, 25, 32))
    dr = ImageDraw.Draw(img)
    for fi in range(n):
        f = frames[fi]
        cx = (fi % cols) * (mw + 1)
        cy = (fi // cols) * (mh + 9)
        for y in range(f["h"]):
            for x in range(f["w"]):
                v = f["px"][y * f["w"] + x]
                if v != 255:
                    img.putpixel((cx + f["x"] + x, cy + 8 + f["y"] + y), pal[v])
        dr.text((cx + 1, cy + 0), str(fi), fill=(120, 220, 120))
    img.save(out_png)
    print("OK", name, n, "frames ->", out_png)


render("unit\\terran\\marine.grp", OUT + "\\all_marine.png")

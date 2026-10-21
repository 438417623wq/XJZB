"""Render test sheets for a handful of GRPs to verify the decoder."""
import os
import struct
from PIL import Image
import sc_archive
import grp as grpm

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
BD = sc_archive.Archive(r"F:\KF\XJZB\BrooDat.mpq")

wpe = SD.read("tileset\\jungle.wpe")
pal = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]  # wpe is BGRA
print("wpe[0:24]:")
for i in range(24):
    print("  %3d  r=%3d g=%3d b=%3d" % (i, pal[i][0], pal[i][1], pal[i][2]))

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
os.makedirs(OUT, exist_ok=True)


def sheet(name, out_png, frames_to_show=None, pal=pal):
    for tag, ar in (("SD", SD), ("BD", BD)):
        if ar.has(name):
            data = ar.read(name)
            break
    else:
        print("MISS", name)
        return None
    frames, mw, mh = grpm.decode_grp(data)
    n = len(frames)
    show = frames_to_show or list(range(n))
    cols = min(len(show), 17)
    rows = (len(show) + cols - 1) // cols
    img = Image.new("RGBA", (cols * mw, rows * mh), (40, 40, 48, 255))
    for k, fi in enumerate(show):
        f = frames[fi]
        ox = (k % cols) * mw
        oy = (k // cols) * mh
        for y in range(f["h"]):
            for x in range(f["w"]):
                v = f["px"][y * f["w"] + x]
                if v != 255:
                    img.putpixel((ox + x, oy + y), pal[v] + (255,))
    img.save(out_png)
    print("OK", name, "frames=%d w=%d h=%d ->" % (n, mw, mh), out_png)
    return frames


sheet("unit\\terran\\marine.grp", OUT + "\\marine.png", frames_to_show=list(range(17)))
sheet("unit\\zerg\\zergling.grp", OUT + "\\zergling.png", frames_to_show=list(range(17)))
sheet("unit\\neutral\\min01.grp", OUT + "\\min01.png", frames_to_show=[0, 1, 2, 3, 4, 5])
sheet("unit\\terran\\control.grp", OUT + "\\control.png", frames_to_show=[0, 1, 2])
sheet("unit\\zerg\\hatchery.grp", OUT + "\\hatchery.png", frames_to_show=[0, 1, 2])

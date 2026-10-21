"""Render gap-aware GRP test sheets."""
import os
from PIL import Image
import sc_archive
import grp as grpm

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
BD = sc_archive.Archive(r"F:\KF\XJZB\BrooDat.mpq")

wpe, wgaps = SD.read_with_gaps("tileset\\jungle.wpe")
pal = [(wpe[i * 4 + 2], wpe[i * 4 + 1], wpe[i * 4]) for i in range(256)]

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
os.makedirs(OUT, exist_ok=True)


def sheet(name, out_png, frames):
    for tag, ar in (("SD", SD), ("BD", BD)):
        if ar.has(name):
            data, gaps = ar.read_with_gaps(name)
            break
    else:
        print("MISS", name)
        return
    allf, mw, mh = grpm.decode_grp(data, gaps)
    cols = min(len(frames), 9)
    rows = (len(frames) + cols - 1) // cols
    img = Image.new("RGB", (cols * mw, rows * mh), (40, 40, 48))
    for k, fi in enumerate(frames):
        if fi >= len(allf):
            continue
        f = allf[fi]
        ox = (k % cols) * mw
        oy = (k // cols) * mh
        for y in range(f["h"]):
            for x in range(f["w"]):
                v = f["px"][y * f["w"] + x]
                if v != 255:
                    img.putpixel((ox + f["x"] + x, oy + f["y"] + y), pal[v])
    img.save(out_png)
    print("OK", name, "total=%d gaps=%d" % (len(allf), len(gaps)), "->", out_png)


sheet("unit\\terran\\marine.grp", OUT + "\\g_marine.png", list(range(17)))
sheet("unit\\terran\\SCV.grp", OUT + "\\g_scv.png", list(range(17)))
sheet("unit\\zerg\\zergling.grp", OUT + "\\g_zergling.png", list(range(17)))
sheet("unit\\terran\\control.grp", OUT + "\\g_control.png", [0, 2, 4])
sheet("unit\\neutral\\min01.grp", OUT + "\\g_min01.png", [0, 1, 2, 3])
sheet("unit\\terran\\tank.grp", OUT + "\\g_tank.png", list(range(17)))

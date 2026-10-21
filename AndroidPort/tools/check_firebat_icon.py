"""Decisive check: is ic_firebat frame 10 or 32?

pipeline_sprites.py says 10, core/Game.java says 32 (and rez/stat_txt.tbl names
32 "Terran Firebat"). One of them ships the wrong artwork. Rather than argue,
render the unit's own GRP frame 0 beside both candidate icons and look.

Run from AndroidPort/tools:  python check_firebat_icon.py
Writes tools/out/firebat_icon_check.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import sc_archive
import grp as grpm
from PIL import Image, ImageDraw

ROOT = r"F:\KF\XJZB"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

# (label, cmdicons frame) plus the unit sprite to compare against
ICON_CANDIDATES = [("ic frame #10", 10), ("ic frame #32", 32),
                   ("ic frame #50", 50)]
SPRITE = ("firebat.grp f0", "unit\\terran\\firebat.grp")

wpe, _ = SD.read_with_gaps("tileset\\jungle.wpe")
PAL = [(wpe[i * 4], wpe[i * 4 + 1], wpe[i * 4 + 2]) for i in range(256)]


def load_grp(path):
    for a in (PT, SD, BD):
        if a.has(path):
            data, gaps = a.read_with_gaps(path)
            return grpm.decode_grp(data, gaps)
    return None


def render(f, scale=3):
    im = Image.new("RGBA", (f["w"], f["h"]), (0, 0, 0, 0))
    px = im.load()
    for y in range(f["h"]):
        for x in range(f["w"]):
            v = f["px"][y * f["w"] + x]
            if v != 255:
                px[x, y] = PAL[v] + (255,)
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def main():
    ci, gaps = SD.read_with_gaps("unit\\cmdbtns\\cmdicons.grp")
    icons, ciw, cih = grpm.decode_grp(ci, gaps)

    cells = []
    for label, idx in ICON_CANDIDATES:
        cells.append((label, render(icons[idx])))
    sp = load_grp(SPRITE[1])
    cells.append((SPRITE[0], render(sp[0][0])))

    cw = max(im.width for _, im in cells) + 24
    ch = max(im.height for _, im in cells) + 34
    img = Image.new("RGB", (cw * len(cells), ch), (30, 32, 40))
    d = ImageDraw.Draw(img)
    for i, (label, im) in enumerate(cells):
        ox = i * cw + (cw - im.width) // 2
        bg = Image.new("RGBA", (im.width, im.height), (30, 32, 40, 255))
        bg.alpha_composite(im, (0, 0))
        img.paste(bg.convert("RGB"), (ox, 28))
        d.text((i * cw + 4, 8), label, fill=(255, 225, 130))
    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, "firebat_icon_check.png")
    img.save(dst)
    print("saved", dst, img.size)
    return 0


if __name__ == "__main__":
    sys.exit(main())

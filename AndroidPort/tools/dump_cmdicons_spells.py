"""Render cmdicons frames 238-390 as labelled grids to hunt for the v2.14
spell-button icons (storm / EMP / yamato / lockdown / d-web / stim)."""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive
import grp as grpm
from pipeline_sprites import BASE_PAL, frame_image

PT = sc_archive.Archive(r"F:\KF\XJZB\patch_rt.mpq")
SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")

data, gaps = None, None
for ar in (PT, SD):
    if ar.has("unit\\cmdbtns\\cmdicons.grp"):
        data, gaps = ar.read_with_gaps("unit\\cmdbtns\\cmdicons.grp")
        break
frames, mw, mh = grpm.decode_grp(data, gaps)
print("frames:", len(frames))

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
for lo, hi in ((238, 314), (314, 390)):
    use = list(range(lo, min(hi, len(frames))))
    cols = 12
    rows = (len(use) + cols - 1) // cols
    cw, ch = mw * 2 + 8, mh * 2 + 14
    img = Image.new("RGBA", (cols * cw, rows * ch), (24, 28, 38, 255))
    d = ImageDraw.Draw(img)
    for k, fi in enumerate(use):
        im = frame_image(frames[fi], BASE_PAL).resize((mw * 2, mh * 2), Image.NEAREST)
        x, y = (k % cols) * cw, (k // cols) * ch
        img.paste(im, (x + 4, y + 4), im)
        d.text((x + 4, y + mh * 2 + 2), str(fi), fill=(180, 210, 235, 255))
    img.save(os.path.join(OUT, "_icons_spellhunt_%d_%d.png" % (lo, hi)))
    print("saved", "_icons_spellhunt_%d_%d.png" % (lo, hi), img.size)

"""One-time channel swap for the already-built map PNGs.

The map chunks and minimaps were rendered with the WPE palette read back-to-front
(B,G,R instead of R,G,B). For terrain the fix is exactly a red/blue channel
swap of the existing pixels: pixel = pal[v], and pal_new[v] == pal_old[v] with
channels 0 and 2 exchanged. Re-decoding the MPQ is not required (and badlands.vx4
/ twilight.vx4 in this repack fail to decompress anyway).

pipeline_maps.py already emits correct RGB for future rebuilds.
"""
import os
import sys
from PIL import Image

MAPS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"


def swap(im):
    r, g, b, a = im.split()
    return Image.merge(im.mode, (b, g, r) + (a,) * (len(im.mode) - 3))


n = 0
for mid in sorted(os.listdir(MAPS)):
    d = os.path.join(MAPS, mid)
    if not os.path.isdir(d):
        continue
    for name in sorted(os.listdir(d)):
        if not name.endswith(".png"):
            continue
        p = os.path.join(d, name)
        im = Image.open(p).convert("RGBA")
        out = swap(im)
        if im.mode == "RGB":
            out = out.convert("RGB")
        out.save(p, optimize=True)
        n += 1
        print("swapped %s/%s" % (mid, name))
print("done, %d files" % n)

"""Are the byte-differing webps pixel-identical? (encoder drift vs real change)"""
import os
from PIL import Image, ImageChops
A = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
W = r"F:\KF\XJZB\AndroidPort\tools\out\_regen_webp"
bad = []
checked = 0
for f in sorted(os.listdir(W)):
    pa, pb = os.path.join(A, f), os.path.join(W, f)
    if not os.path.isfile(pa):
        continue
    ia = Image.open(pa).convert("RGBA")
    ib = Image.open(pb).convert("RGBA")
    checked += 1
    if ia.size != ib.size:
        bad.append((f, "size %s vs %s" % (ia.size, ib.size)))
        continue
    if ImageChops.difference(ia, ib).getbbox() is not None:
        bad.append((f, "pixels differ"))
print("checked=%d pixel_mismatch=%d" % (checked, len(bad)))
for b in bad[:30]:
    print("  ", b)

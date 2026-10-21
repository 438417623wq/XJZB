# Detect the command-card's 3x3 slot rectangles from the screenshot so tap
# coordinates come from the real render rather than a hand-computed layout.
import os
import numpy as np
from PIL import Image

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
im = Image.open(os.path.join(OUT, "_e42_build1.png")).convert("RGB")
a = np.asarray(im).astype(np.int16)
H, W = a.shape[:2]
print("screenshot", W, "x", H)

# The card lives in the bottom-right. Slot interiors are a dark blue-grey that
# is clearly lighter than the near-black page background.
x0, y0 = int(W * 0.78), int(H * 0.58)
sub = a[y0:, x0:]
lum = sub.mean(axis=2)

# slot fill is roughly 30..70 luminance; background is < 20
mask = (lum > 26) & (lum < 110)
colsum = mask.sum(axis=0)
rowsum = mask.sum(axis=1)

def runs(profile, min_len):
    out = []
    start = None
    for i, v in enumerate(profile):
        on = v > min_len
        if on and start is None:
            start = i
        elif not on and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(profile) - 1))
    return out

cruns = runs(colsum, sub.shape[0] * 0.10)
rruns = runs(rowsum, sub.shape[1] * 0.10)
print("column runs (device x):", [(x0 + s, x0 + e) for s, e in cruns])
print("row runs    (device y):", [(y0 + s, y0 + e) for s, e in rruns])

cols = [x0 + (s + e) // 2 for s, e in cruns]
rows = [y0 + (s + e) // 2 for s, e in rruns]
print("column centers:", cols)
print("row centers   :", rows)
if len(cols) == 3 and len(rows) == 3:
    print()
    for ri, cy in enumerate(rows):
        for ci, cx in enumerate(cols):
            print(f"  cell row{ri+1} col{ci+1}: tap {cx} {cy}")

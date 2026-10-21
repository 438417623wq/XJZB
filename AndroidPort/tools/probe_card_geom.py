"""Locate the 3x3 command-card cell rectangles in a device screenshot.

A cell edge is a ~100 px long bright bevel run, so per-row/column bright
counts spike where three cell edges line up.  Printing those spikes gives
the exact tap targets, which matters because a tap that lands in the
inter-cell gap silently does nothing.
"""
import sys
import numpy as np
from PIL import Image

path = sys.argv[1] if len(sys.argv) > 1 else r"F:\KF\XJZB\AndroidPort\tools\out\device\nc.png"
im = np.array(Image.open(path).convert("RGB")).astype(int)
H, W, _ = im.shape
print("image", W, "x", H)

y0, y1 = int(H * 0.55), H
x0, x1 = int(W * 0.75), W
s = im[y0:y1, x0:x1].sum(axis=2)
print("region", x0, y0, "->", x1, y1, " fill median", int(np.median(s)))

rowcount = (s > 300).sum(axis=1)
colcount = (s > 300).sum(axis=0)

print("\nrows with >=120 bright px (candidate horizontal bevels):")
for i, v in enumerate(rowcount):
    if v >= 120:
        print(f"  y={y0+i}  n={v}")

print("\ncols with >=60 bright px (candidate vertical bevels):")
for i, v in enumerate(colcount):
    if v >= 60:
        print(f"  x={x0+i}  n={v}")

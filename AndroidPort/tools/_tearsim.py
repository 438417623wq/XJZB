"""Reproduce the reported black bar from the two cameras fitted out of a2.jpg.

A torn frame is drawn by two cameras: render() walks chunks cy outer, cx inner,
so everything before the write lands with camera A and everything after with
camera B.  The gap is wherever neither camera's dst covers a pixel.  If the
fitted cameras are the real cause, this mask must match the measured green mask
of a2.jpg -- same staircase, same extent.
"""
import sys
import numpy as np
from PIL import Image

W, H, CS = 2608, 1200, 512
WPX, HPX = 2048, 2048
BLEED = 4

# fitted out of a2.jpg by _camfit2.py: upper band vs lower band
A = (1.543, 849.0, 500.0)     # drawn first (top of the frame)
B = (1.561, 858.0, 413.5)     # drawn after the mid-frame write


def mask_for(z, camx, camy):
    """Screen pixels covered by the chunk dsts of one camera."""
    m = np.zeros((H, W), dtype=bool)
    cx0 = max(0, int(((0 - camx) * z + W / 2) // CS))
    cx1 = min((WPX - 1) // CS, int(((W - camx) * z + W / 2) // CS))
    cy0 = max(0, int(((0 - camy) * z + H / 2) // CS))
    cy1 = min((HPX - 1) // CS, int(((H - camy) * z + H / 2) // CS))
    for cy in range(cy0, cy1 + 1):
        for cx in range(cx0, cx1 + 1):
            import math
            dx0 = math.floor((cx * CS - camx) * z + W / 2)
            dy0 = math.floor((cy * CS - camy) * z + H / 2)
            dx1 = math.floor((min(cx * CS + CS, WPX) - camx) * z + W / 2) + BLEED
            dy1 = math.floor((min(cy * CS + CS, HPX) - camy) * z + H / 2) + BLEED
            x0, x1 = max(0, dx0), min(W, dx1)
            y0, y1 = max(0, dy0), min(H, dy1)
            if x1 > x0 and y1 > y0:
                m[y0:y1, x0:x1] = True
    return m


def torn_mask(zA, xA, yA, zB, xB, yB, split_cy, split_cx):
    """One frame, two cameras, split mid-iteration."""
    import math
    m = np.zeros((H, W), dtype=bool)
    for cy in range(0, HPX // CS):
        for cx in range(0, WPX // CS):
            after = (cy > split_cy) or (cy == split_cy and cx >= split_cx)
            z, camx, camy = (zB, xB, yB) if after else (zA, xA, yA)
            dx0 = math.floor((cx * CS - camx) * z + W / 2)
            dy0 = math.floor((cy * CS - camy) * z + H / 2)
            dx1 = math.floor((min(cx * CS + CS, WPX) - camx) * z + W / 2) + BLEED
            dy1 = math.floor((min(cy * CS + CS, HPX) - camy) * z + H / 2) + BLEED
            x0, x1 = max(0, dx0), min(W, dx1)
            y0, y1 = max(0, dy0), min(H, dy1)
            if x1 > x0 and y1 > y0:
                m[y0:y1, x0:x1] = True
    return m


def stats(name, mask, measured=None):
    gap = ~mask
    rows = np.where(gap.any(axis=1))[0]
    cols = np.where(gap.any(axis=0))[0]
    print(f"{name}: uncovered px={int(gap.sum())}", end="")
    if len(rows):
        print(f" rows {rows.min()}..{rows.max()} (h={rows.max()-rows.min()+1})", end="")
    if len(cols):
        print(f" cols {cols.min()}..{cols.max()}", end="")
    print()
    if measured is not None and len(rows):
        inter = (gap & measured).sum()
        print(f"    overlap with measured green mask: {inter} px"
              f"  (sim {int(gap.sum())}, measured {int(measured.sum())})")
        print(f"    of the simulated gap, {100.0*inter/max(1,gap.sum()):.1f}% is green on device")
        print(f"    of the measured green, {100.0*inter/max(1,measured.sum()):.1f}% is predicted")


if __name__ == "__main__":
    # measured green mask of a2.jpg
    img = np.asarray(Image.open(r"C:\Users\XiaoXin\AppData\Local\Temp\xjzb_shots\a2.jpg").convert("RGB")).astype(int)
    g, r, b = img[:, :, 1], img[:, :, 0], img[:, :, 2]
    green = (g > 185) & (r < 105) & (b < 105)
    print("a2.jpg green:", int(green.sum()), "px")

    print("\n-- single camera (the fix): every seam must overlap --")
    stats("A only", mask_for(*A))
    stats("B only", mask_for(*B))

    print("\n-- torn frame: split mid-iteration --")
    best = None
    for split_cy in range(0, 4):
        for split_cx in range(0, 4):
            m = torn_mask(*A, *B, split_cy, split_cx)
            gap = ~m
            rows = np.where(gap.any(axis=1))[0]
            h = (rows.max() - rows.min() + 1) if len(rows) else 0
            inter = (gap & green).sum()
            cov = inter / max(1, green.sum())
            print(f"  split cy={split_cy} cx={split_cx}: gap={int(gap.sum())} h={h} "
                  f"green-covered={100.0*cov:.1f}%")
            if best is None or cov > best[0]:
                best = (cov, split_cy, split_cx, m)
    cov, scy, scx, m = best
    print(f"\nbest split: cy={scy} cx={scx}")
    stats("predicted gap", m, green)

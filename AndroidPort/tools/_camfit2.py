"""Fit the camera of each REGION of a captured frame independently.

The on-screen panel prints cam=(camX,camY) at the END of the frame; the terrain
is drawn at the START of the same frame. If those two disagree, the frame is not
internally consistent -- which is the only way bare canvas can be left between
chunk rectangles that tile exactly when the camera holds still.

This recovers the camera each region of the shot was drawn with, by brute-force
least squares against the shipped chunk assets (zoom fixed, bilinear sampling).
"""
import os
import sys
import numpy as np
from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide"
SHOTS = r"C:\Users\XiaoXin\AppData\Local\Temp\xjzb_shots"
CS = 512
W, H = 2608, 1200
ZOOM = 1.56


def world_image():
    w = Image.new("RGB", (2048, 2048), (0, 0, 0))
    for cy in range(4):
        for cx in range(4):
            w.paste(Image.open(os.path.join(ASSETS, "c_%d_%d.webp" % (cx, cy))).convert("RGB"),
                    (cx * CS, cy * CS))
    return np.asarray(w).astype(np.float32)


def sample(world, wx, wy):
    """Bilinear sample of the world image at float coords."""
    wx = np.clip(wx, 0, 2046.5)
    wy = np.clip(wy, 0, 2046.5)
    x0 = np.floor(wx).astype(np.int32)
    y0 = np.floor(wy).astype(np.int32)
    fx = (wx - x0)[..., None]
    fy = (wy - y0)[..., None]
    a = world[y0, x0]
    b = world[y0, x0 + 1]
    c = world[y0 + 1, x0]
    d = world[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fit(world, shot, region, step=4, rng=None):
    x0, x1, y0, y1 = region
    ys, xs = np.mgrid[y0:y1:8, x0:x1:8]
    xs = xs.astype(np.float64)
    ys = ys.astype(np.float64)
    tgt = shot[y0:y1:8, x0:x1:8]
    bx = (xs - W / 2.0) / ZOOM
    by = (ys - H / 2.0) / ZOOM
    if rng is None:
        cxs = np.arange(650, 1150, step)
        cys = np.arange(350, 1300, step)
    else:
        cxs = np.arange(rng[0], rng[1], step)
        cys = np.arange(rng[2], rng[3], step)
    best = None
    for camX in cxs:
        for camY in cys:
            exp = sample(world, bx + camX, by + camY)
            s = float(np.abs(exp - tgt).mean())
            if best is None or s < best[0]:
                best = (s, float(camX), float(camY))
    return best


def main():
    world = world_image()
    plan = {
        "a1.jpg": [("above-L", (100, 700, 600, 780)), ("below-L", (100, 700, 830, 1010)),
                   ("above-R", (900, 1450, 610, 790)), ("below-R", (900, 1450, 830, 1010)),
                   ("top-R", (1700, 2400, 200, 500))],
        "a2.jpg": [("above-L", (100, 700, 400, 610)), ("below-L", (100, 700, 765, 975)),
                   ("above-M", (900, 1500, 440, 650)), ("below-M", (900, 1500, 765, 975)),
                   ("above-R", (1700, 2300, 480, 685)), ("below-R", (1700, 2300, 765, 975))],
    }
    for name, regions in plan.items():
        shot = np.asarray(Image.open(os.path.join(SHOTS, name)).convert("RGB")).astype(np.float32)
        print("== %s" % name)
        for label, reg in regions:
            s, cx, cy = fit(world, shot, reg, step=8)
            for _ in range(3):
                s, cx, cy = fit(world, shot, reg, step=2,
                                rng=(cx - 10, cx + 10.1, cy - 10, cy + 10.1))
                s, cx, cy = fit(world, shot, reg, step=0.5,
                                rng=(cx - 2, cx + 2.1, cy - 2, cy + 2.1))
            print("   %-8s %-22s -> cam=(%8.1f, %8.1f)   mean|diff| %.2f"
                  % (label, str(reg), cx, cy, s))
            sys.stdout.flush()


if __name__ == "__main__":
    main()

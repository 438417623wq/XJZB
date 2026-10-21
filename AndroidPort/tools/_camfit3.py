"""Fit the camera of each REGION of a captured frame independently (2D fit).

Green in the shot is render()'s diagnostic clear colour, so those pixels were
never drawn. The remaining question is whether the whole frame used ONE camera:
the render thread re-reads camX/camY/zoom for every coordinate it converts while
the touch thread writes them, so a single frame can be a mosaic of strips drawn
at different cameras -- and mosaic strips no longer tile, which is exactly how
bare canvas survives between chunk rectangles that tile perfectly when the
camera holds still.

For each region this does a proper 2D least-squares fit of (camX, camY) against
the shipped chunk assets, sampling the world image bilinearly (as the game's
FILTER_BITMAP_FLAG chunk paint does). Separable sampling keeps it fast.
"""
import os
import sys
import numpy as np
from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide"
SHOTS = r"C:\Users\XiaoXin\AppData\Local\Temp\xjzb_shots"
CS = 512
W, H = 2608, 1200


def world_image():
    w = Image.new("RGB", (2048, 2048), (0, 0, 0))
    for cy in range(4):
        for cx in range(4):
            w.paste(Image.open(os.path.join(ASSETS, "c_%d_%d.webp" % (cx, cy))).convert("RGB"),
                    (cx * CS, cy * CS))
    return np.asarray(w).astype(np.float32)


def bilinear_rows(world, ycoord):
    """world rows sampled at float y (clamped), shape (len(y), 2048, 3)."""
    y = np.clip(ycoord, 0, 2046.5)
    y0 = np.floor(y).astype(np.int32)
    fy = (y - y0)[:, None, None]
    return world[y0] * (1 - fy) + world[y0 + 1] * fy


def bilinear_cols(rows, xcoord):
    """world columns sampled at float x, shape (len(y), len(x), 3)."""
    x = np.clip(xcoord, 0, 2046.5)
    x0 = np.floor(x).astype(np.int32)
    fx = (x - x0)[None, :, None]
    a = rows[:, x0]
    b = rows[:, x0 + 1]
    return a * (1 - fx) + b * fx


def fit(world, shot, region, zoom, cx0, cx1, cy0, cy1, step):
    x0, x1, y0, y1 = region
    step_px = 8
    ys = np.arange(y0, y1, step_px, dtype=np.float64)
    xs = np.arange(x0, x1, step_px, dtype=np.float64)
    tgt = shot[y0:y1:step_px, x0:x1:step_px]
    bx = (xs - W / 2.0) / zoom
    by = (ys - H / 2.0) / zoom
    best = None
    cys = np.arange(cy0, cy1, step)
    cxs = np.arange(cx0, cx1, step)
    for camY in cys:
        rows = bilinear_rows(world, by + camY)
        for camX in cxs:
            exp = bilinear_cols(rows, bx + camX)
            s = float(np.abs(exp - tgt).mean())
            if best is None or s < best[0]:
                best = (s, float(camX), float(camY))
    return best


def fit_region(world, shot, region, zoom):
    s, cx, cy = fit(world, shot, region, zoom, 600, 1200, 300, 1400, 8)
    s, cx, cy = fit(world, shot, region, zoom, cx - 9, cx + 9.1, cy - 9, cy + 9.1, 2)
    s, cx, cy = fit(world, shot, region, zoom, cx - 2, cx + 2.1, cy - 2, cy + 2.1, 0.5)
    return s, cx, cy


def main():
    zoom = float(sys.argv[1]) if len(sys.argv) > 1 else 1.56
    world = world_image()
    plan = {
        "a1.jpg": [("above-L", (60, 660, 600, 780)), ("below-L", (60, 660, 830, 1010)),
                   ("above-R", (880, 1440, 620, 790)), ("below-R", (880, 1440, 830, 1010)),
                   ("top-R", (1700, 2400, 220, 520))],
        "a2.jpg": [("above-L", (60, 660, 380, 605)), ("below-L", (60, 660, 765, 980)),
                   ("above-M", (880, 1480, 430, 645)), ("below-M", (880, 1480, 765, 980)),
                   ("above-R", (1660, 2280, 480, 685)), ("below-R", (1660, 2280, 765, 980))],
    }
    for name, regions in plan.items():
        shot = np.asarray(Image.open(os.path.join(SHOTS, name)).convert("RGB")).astype(np.float32)
        print("== %s   (zoom %.3f)" % (name, zoom))
        for label, reg in regions:
            s, cx, cy = fit_region(world, shot, reg, zoom)
            print("   %-8s %-22s -> cam=(%8.1f,%8.1f)  mean|diff| %5.2f"
                  % (label, str(reg), cx, cy, s))
            sys.stdout.flush()


if __name__ == "__main__":
    main()

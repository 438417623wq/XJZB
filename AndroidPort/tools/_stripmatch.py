"""Recover, per screen strip, the camera the terrain in that strip was drawn with.

Green in the shot is render()'s diagnostic clear colour, so those pixels were
never drawn -- that part is settled. What is not settled is whether the whole
frame used ONE camera. The render thread reads camX/camY/zoom afresh for every
coordinate it converts, while the touch thread writes them, so a frame can be a
mosaic of strips drawn at different cameras; the chunk dsts then no longer tile
and bare canvas shows through between them.

For each strip of the shot this matches the vertical colour profile against the
world image, which recovers the camY that strip was drawn with. Strips drawn
with different camY mean the frame is internally inconsistent.
"""
import os
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


def world_profile(world, wx0, wx1):
    """Mean colour per world row over a world-x window."""
    return world[:, wx0:wx1, :].mean(axis=1)          # (2048, 3)


def strip_camY(world, shot, x0, x1, y0, y1, camX):
    """camY that best explains the shot's rows y0..y1 in columns x0..x1."""
    wx0 = int(np.clip((x0 - W / 2.0) / ZOOM + camX, 0, 2047))
    wx1 = int(np.clip((x1 - W / 2.0) / ZOOM + camX, 0, 2047))
    if wx1 <= wx0:
        return None
    wp = world_profile(world, wx0, wx1)
    sp = shot[y0:y1, x0:x1, :].mean(axis=1)           # (n, 3)
    ys = np.arange(y0, y1)
    best = None
    for camY in np.arange(300.0, 1400.0, 0.5):
        wy = np.clip(np.round((ys - H / 2.0) / ZOOM + camY).astype(int), 0, 2047)
        d = np.abs(wp[wy] - sp).mean()
        if best is None or d < best[0]:
            best = (d, camY)
    return best


def main():
    world = world_image()
    for name, camX, strips in (
            ("a2.jpg", 890, [(100, 700, 420, 615), (100, 700, 760, 950),
                             (900, 1500, 460, 655), (900, 1500, 765, 955),
                             (1700, 2300, 500, 690), (1700, 2300, 765, 955)]),
            ("a1.jpg", 832, [(100, 700, 600, 788), (100, 700, 820, 1000),
                             (900, 1450, 610, 798), (900, 1450, 820, 1000)])):
        shot = np.asarray(Image.open(os.path.join(SHOTS, name)).convert("RGB")).astype(np.float32)
        print("== %s   panel cam=(%d,?)" % (name, camX))
        for (x0, x1, y0, y1) in strips:
            r = strip_camY(world, shot, x0, x1, y0, y1, camX)
            if r is None:
                continue
            d, camY = r
            print("   x %4d..%4d  y %4d..%4d  -> camY = %7.1f   mean|diff| %.2f"
                  % (x0, x1, y0, y1, camY, d))


if __name__ == "__main__":
    main()

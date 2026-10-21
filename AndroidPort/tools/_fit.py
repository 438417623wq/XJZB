"""Fit the camera of a captured frame against the shipped assets.

The screenshots contain a pure-green band -- render()'s diagnostic clear colour,
i.e. pixels no draw covered. Before blaming the chunk-dst maths, this recovers
the camera the TERRAIN in the shot was actually drawn with, and compares it with
the value the on-screen panel printed in the same frame. If the two disagree the
frame is not a single consistent render, which points at the camera being read
repeatedly while another thread mutates it.
"""
import os
import numpy as np
from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide"
SHOTS = r"C:\Users\XiaoXin\AppData\Local\Temp\xjzb_shots"
CS = 512
W, H = 2608, 1200
DOWN = 4


def world_image():
    w = Image.new("RGB", (2048, 2048), (255, 0, 255))
    for cy in range(4):
        for cx in range(4):
            w.paste(Image.open(os.path.join(ASSETS, "c_%d_%d.webp" % (cx, cy))).convert("RGB"),
                    (cx * CS, cy * CS))
    return np.asarray(w).astype(np.float32)


def render(world, zoom, camX, camY):
    w = W // DOWN
    h = H // DOWN
    ys = np.arange(h, dtype=np.float64) * DOWN + DOWN / 2.0
    xs = np.arange(w, dtype=np.float64) * DOWN + DOWN / 2.0
    wy = (ys - H / 2.0) / zoom + camY
    wx = (xs - W / 2.0) / zoom + camX
    iy = np.clip(np.round(wy).astype(int), 0, 2047)
    ix = np.clip(np.round(wx).astype(int), 0, 2047)
    return world[np.ix_(iy, ix)]


def main():
    world = world_image()
    for name, panel in (("a1.jpg", (832, 501)), ("a2.jpg", (890, 882))):
        shot = np.asarray(Image.open(os.path.join(SHOTS, name)).convert("RGB")).astype(np.float32)
        small = shot[::DOWN, ::DOWN]
        hh, ww, _ = small.shape
        R, G, B = small[:, :, 0], small[:, :, 1], small[:, :, 2]
        green = (G > 185) & (R < 105) & (B < 105)
        yy, xx = np.mgrid[0:hh, 0:ww]
        # exclude the green band, the diagnostic panel and the HUD strip
        keep = (~green) & (yy * DOWN > 320) & (yy * DOWN < 1120)
        keep &= ~((xx * DOWN < 800) & (yy * DOWN < 300))
        print("== %s  panel cam=%s  usable px=%d" % (name, panel, keep.sum()))
        best = None
        for zoom in (1.52, 1.54, 1.56, 1.58, 1.60):
            for camX in range(560, 1120, 6):
                for camY in range(300, 1000, 6):
                    exp = render(world, zoom, camX, camY)
                    d = np.abs(exp - small).mean(axis=2)
                    s = float(d[keep].mean())
                    if best is None or s < best[0]:
                        best = (s, zoom, camX, camY)
        s, zoom, camX, camY = best
        print("   coarse best: zoom=%.2f cam=(%d,%d)  mean|diff|=%.2f" % (zoom, camX, camY, s))
        # refine
        for zz in np.arange(zoom - 0.02, zoom + 0.021, 0.005):
            for cxx in range(camX - 8, camX + 9, 2):
                for cyy in range(camY - 8, camY + 9, 2):
                    exp = render(world, zz, cxx, cyy)
                    d = np.abs(exp - small).mean(axis=2)
                    ss = float(d[keep].mean())
                    if ss < s:
                        s, zoom, camX, camY = ss, zz, cxx, cyy
        print("   refined    : zoom=%.3f cam=(%d,%d)  mean|diff|=%.2f" % (zoom, camX, camY, s))
        exp = render(world, zoom, camX, camY)
        d = np.abs(exp - small).mean(axis=2)
        vis = np.zeros((hh, ww, 3), np.uint8)
        vis[..., 0] = np.clip(d * 2, 0, 255)
        vis[green] = (0, 255, 0)
        Image.fromarray(vis).save(
            r"F:\KF\XJZB\AndroidPort\tools\out\_fit_%s" % name.replace(".jpg", ".png"))
        # predicted chunk grid for this camera
        print("   chunk grid at fitted camera (dst, no bleed):")
        for cy in range(4):
            dy0 = (cy * CS - camY) * zoom + H / 2.0
            dy1 = (min((cy + 1) * CS, 2048) - camY) * zoom + H / 2.0
            print("      row %d  y %8.1f .. %8.1f" % (cy, dy0, dy1))
        for cx in range(4):
            dx0 = (cx * CS - camX) * zoom + W / 2.0
            dx1 = (min((cx + 1) * CS, 2048) - camX) * zoom + W / 2.0
            print("      col %d  x %8.1f .. %8.1f" % (cx, dx0, dx1))


if __name__ == "__main__":
    main()

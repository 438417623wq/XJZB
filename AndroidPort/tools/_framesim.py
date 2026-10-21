"""Reproduce the captured frame from the shipped divide chunks.

The screenshots show a pure-green band. Green is render()'s diagnostic clear
colour, so the band is a place where NO chunk covered the canvas. The chunk-dst
geometry is provably gapless (see _geomsim.py), so the band must come from
something else -- this script settles it by rebuilding the frame from the
assets and diffing against the screenshot.
"""
import os
import sys
import numpy as np
from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide"
SHOTS = r"C:\Users\XiaoXin\AppData\Local\Temp\xjzb_shots"
CS = 512


def world_image():
    w = Image.new("RGB", (2048, 2048), (255, 0, 255))
    for cy in range(4):
        for cx in range(4):
            p = os.path.join(ASSETS, "c_%d_%d.webp" % (cx, cy))
            w.paste(Image.open(p).convert("RGB"), (cx * CS, cy * CS))
    return np.asarray(w).astype(np.int16)


def render(world, W, H, zoom, camX, camY, anchorY=None):
    if anchorY is None:
        anchorY = H / 2.0
    ys = np.arange(H, dtype=np.float64)
    xs = np.arange(W, dtype=np.float64)
    wy = (ys - anchorY) / zoom + camY
    wx = (xs - W / 2.0) / zoom + camX
    iy = np.clip(np.round(wy).astype(int), 0, world.shape[0] - 1)
    ix = np.clip(np.round(wx).astype(int), 0, world.shape[1] - 1)
    return world[np.ix_(iy, ix)]


def band_of(a):
    pure = (a[:, :, 1] > 185) & (a[:, :, 0] < 105) & (a[:, :, 2] < 105)
    rows = np.where(pure.sum(axis=1) > a.shape[1] * 0.2)[0]
    return pure, rows


def main():
    world = world_image()
    for name in ("a1.jpg", "a2.jpg"):
        shot = np.asarray(Image.open(os.path.join(SHOTS, name)).convert("RGB")).astype(np.int16)
        H, W, _ = shot.shape
        pure, band_rows = band_of(shot)
        print("== %s  %dx%d  green rows %s..%s"
              % (name, W, H, band_rows.min() if len(band_rows) else "-",
                 band_rows.max() if len(band_rows) else "-"))
        # the panel reports the camera; try the reported value and neighbours
        cands = [(832, 501), (836, 385), (855, 501), (892, 882), (1590, 882), (892, 388)]
        best = None
        for (cx, cy) in cands:
            exp = render(world, W, H, 1.56, cx, cy)
            valid = ~pure
            d = np.abs(exp - shot).mean(axis=2)
            score = float(d[valid].mean())
            if best is None or score < best[0]:
                best = (score, cx, cy, exp, d)
        score, cx, cy, exp, d = best
        print("   best cam=(%d,%d) mean|diff| outside band = %.2f" % (cx, cy, score))
        # per-20-row diff profile
        print("   row  meanDiff  greenFrac")
        for y in range(0, H, 40):
            sl = slice(y, min(H, y + 40))
            print("   %4d  %8.2f   %5.3f" % (y, float(d[sl].mean()), float(pure[sl].mean())))
        # what world y do the band edges map to
        for y in (band_rows.min(), band_rows.max()) if len(band_rows) else ():
            print("   band edge y=%d -> world y=%.1f  chunkRow=%d  localY=%.1f"
                  % (y, (y - H / 2.0) / 1.56 + cy, int(((y - H / 2.0) / 1.56 + cy) // CS),
                     ((y - H / 2.0) / 1.56 + cy) % CS))
        vis = np.zeros((H, W, 3), np.uint8)
        vis[..., 1] = np.where(pure, 255, 0)
        vis[~pure] = (shot[~pure] // 3).astype(np.uint8)
        Image.fromarray(vis).resize((W // 3, H // 3)).save(
            r"F:\KF\XJZB\AndroidPort\tools\out\_cmp_%s" % name.replace(".jpg", ".png"))


if __name__ == "__main__":
    main()

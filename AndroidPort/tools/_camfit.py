"""Recover the camera the TERRAIN in a captured frame was really drawn with.

The on-screen diagnostic panel prints cam=(camX,camY) at the END of the frame
(drawHud runs last). The terrain is drawn at the START of the same frame. If the
camera moved in between -- the touch handler writes camX/camY from the UI thread
while the render thread reads them unsynchronised -- the printed value is not the
one the terrain used, and the mismatch can leave bare canvas on screen.

This finds the terrain's own camera by normalised cross-correlation: the world
image is resampled into screen space at the reported zoom, so a plain translation
search recovers (camX, camY) directly.
"""
import os
import numpy as np
from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide"
SHOTS = r"C:\Users\XiaoXin\AppData\Local\Temp\xjzb_shots"
CS = 512
W, H = 2608, 1200


def world_image():
    w = Image.new("RGB", (2048, 2048), (255, 0, 255))
    for cy in range(4):
        for cx in range(4):
            w.paste(Image.open(os.path.join(ASSETS, "c_%d_%d.webp" % (cx, cy))).convert("RGB"),
                    (cx * CS, cy * CS))
    return w


def ncc(a, t):
    """Normalised cross-correlation of template t over image a (valid region)."""
    na, ma = a.shape
    nt, mt = t.shape
    fs = (na + nt, ma + mt)
    A = np.fft.rfft2(a, fs)
    T = np.fft.rfft2(t[::-1, ::-1], fs)
    corr = np.fft.irfft2(A * T, fs)[nt - 1:na, mt - 1:ma]
    # local energy of a
    ones = np.ones_like(t)
    O = np.fft.rfft2(ones[::-1, ::-1], fs)
    e = np.fft.irfft2(np.fft.rfft2(a * a, fs) * O, fs)[nt - 1:na, mt - 1:ma]
    e = np.maximum(e, 1e-6)
    return corr / np.sqrt(e * float((t * t).sum()))


def main():
    world = world_image()
    for name, panel in (("a1.jpg", (832, 501)), ("a2.jpg", (890, 882))):
        shot = Image.open(os.path.join(SHOTS, name)).convert("RGB")
        arr = np.asarray(shot).astype(np.float32)
        R, G, B = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        green = (G > 185) & (R < 105) & (B < 105)
        gray = arr.mean(axis=2)
        # only trust terrain pixels: drop the green band, the panel, the HUD
        yy, xx = np.mgrid[0:H, 0:W]
        trust = (~green) & (yy > 330) & (yy < 1105) & ~((xx < 800) & (yy < 310))
        print("== %s  panel says cam=%s  trusted px=%d" % (name, panel, trust.sum()))
        for zoom in (1.50, 1.53, 1.56, 1.59):
            big = world.resize((int(round(2048 * zoom)), int(round(2048 * zoom))),
                               Image.BILINEAR)
            bg = np.asarray(big).mean(axis=2)
            # template: a clean terrain block from the middle of the screen
            t = gray[400:900, 900:1700]
            tm = trust[400:900, 900:1700]
            t = np.where(tm, t, t[tm].mean())
            t = t - t.mean()
            res = ncc(bg, t)
            idx = np.unravel_index(np.argmax(res), res.shape)
            v, u = int(idx[0]), int(idx[1])       # top-left of the template in `big`
            # big(u,v) corresponds to screen x = u - (camX*zoom - W/2)
            camX = (u + W / 2.0 - 900) / zoom
            camY = (v + H / 2.0 - 400) / zoom
            print("   zoom=%.2f  ncc=%.4f  -> cam=(%.1f, %.1f)" % (zoom, res[idx], camX, camY))


if __name__ == "__main__":
    main()

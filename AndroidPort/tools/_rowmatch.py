"""Locate the captured frame inside the map by matching whole pixel rows.

The screenshots show a pure-green band, which is render()'s diagnostic clear
colour: no draw covered those pixels. Rather than guess which chunk failed, this
script recovers the y-mapping the frame actually used -- for every screen row it
finds the world row whose pixels match -- so a discontinuity in that mapping
shows exactly where content is missing and by how much.
"""
import os
import numpy as np
from PIL import Image

ASSETS = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide"
SHOTS = r"C:\Users\XiaoXin\AppData\Local\Temp\xjzb_shots"
CS = 512


def world_image():
    w = Image.new("RGB", (2048, 2048), (255, 0, 255))
    for cy in range(4):
        for cx in range(4):
            w.paste(Image.open(os.path.join(ASSETS, "c_%d_%d.webp" % (cx, cy))).convert("RGB"),
                    (cx * CS, cy * CS))
    return np.asarray(w).astype(np.float32)


def main():
    world = world_image()
    W, H = 2608, 1200
    zoom = 1.56
    for name, camX, camY, y0, y1 in (("a2.jpg", 890, 882, 300, 1150),
                                     ("a1.jpg", 832, 501, 500, 1100)):
        shot = np.asarray(Image.open(os.path.join(SHOTS, name)).convert("RGB")).astype(np.float32)
        xr = np.arange(1600, 2400)
        wxr = np.round((xr - W / 2.0) / zoom + camX).astype(int)
        wxr = np.clip(wxr, 0, 2047)
        rows = world[:, wxr].reshape(2048, -1)    # (2048, n*3) world rows at those wx
        ys = np.arange(y0, y1)
        cur = shot[ys][:, xr].reshape(len(ys), -1)  # (n, n*3)
        # SSD of every screen row against every world row
        a2 = (cur ** 2).sum(axis=1)[:, None]
        b2 = (rows ** 2).sum(axis=1)[None, :]
        cross = cur @ rows.T
        ssd = a2 + b2 - 2 * cross
        best = ssd.argmin(axis=1)
        print("== %s cam=(%d,%d) zoom=%.2f" % (name, camX, camY, zoom))
        print("   y  -> best world wy   (expected %.1f)   ssd"
              % ((ys[0] - 600) / zoom + camY))
        prev = None
        for i, y in enumerate(ys):
            wy = best[i]
            exp = (y - 600) / zoom + camY
            if prev is None or abs(int(wy) - int(prev)) > 2 or i % 50 == 0:
                print("   %4d -> %5d   exp %7.1f   d=%+6.1f   ssd=%10.0f"
                      % (y, wy, exp, wy - exp, ssd[i, wy]))
            prev = wy
        # fit slope over the clean stretches
        lin = np.polyfit(ys, best, 1)
        print("   global fit: wy = %.4f*y + %.1f  (slope should be 1/zoom = %.4f)"
              % (lin[0], lin[1], 1 / zoom))


if __name__ == "__main__":
    main()

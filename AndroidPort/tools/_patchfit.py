"""Recover the camera each SCREEN PATCH of a captured frame was drawn with.

Green in the shot is render()'s diagnostic clear colour, so those pixels were
never drawn. That much is settled. What is not settled is whether the frame used
ONE camera for all of its terrain (a coverage bug) or SEVERAL (the render thread
re-reading camX/camY while the touch thread mutates them). Every patch of the
shot is matched back into the world image independently: if the per-patch
cameras disagree, the frame itself is internally inconsistent.
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
    w = Image.new("RGB", (2048, 2048), (255, 0, 255))
    for cy in range(4):
        for cx in range(4):
            w.paste(Image.open(os.path.join(ASSETS, "c_%d_%d.webp" % (cx, cy))).convert("RGB"),
                    (cx * CS, cy * CS))
    return np.asarray(w).astype(np.float32).mean(axis=2)


def ncc_full(img, t):
    na, ma = img.shape
    nt, mt = t.shape
    fs = (na + nt, ma + mt)
    A = np.fft.rfft2(img, fs)
    T = np.fft.rfft2(t[::-1, ::-1], fs)
    corr = np.fft.irfft2(A * T, fs)[nt - 1:na, mt - 1:ma]
    O = np.fft.rfft2(np.ones_like(t)[::-1, ::-1], fs)
    e = np.fft.irfft2(np.fft.rfft2(img * img, fs) * O, fs)[nt - 1:na, mt - 1:ma]
    return corr / np.sqrt(np.maximum(e, 1e-6) * float((t * t).sum()))


def main():
    world = world_image()
    for name, panel in (("a1.jpg", (832, 501)), ("a2.jpg", (890, 882))):
        shot = Image.open(os.path.join(SHOTS, name)).convert("RGB")
        sw, sh = int(round(W / ZOOM)), int(round(H / ZOOM))
        small = np.asarray(shot.resize((sw, sh), Image.BILINEAR)).astype(np.float32).mean(axis=2)
        print("== %s  panel cam=%s   (world-scale shot %dx%d)" % (name, panel, sw, sh))
        # screen-space probe points, avoiding the panel, the HUD and the green band
        probes = [(900, 380), (1500, 380), (2100, 380), (2450, 380),
                  (900, 1000), (1500, 1000), (2100, 1000), (2450, 1000),
                  (700, 600), (2450, 600)]
        est = []
        for (sx0, sy0) in probes:
            pw = ph = 100
            if sx0 + pw > W or sy0 + ph > H:
                continue
            wx0 = int(round(sx0 / ZOOM)); wy0 = int(round(sy0 / ZOOM))
            ww = int(round(pw / ZOOM)); wh = int(round(ph / ZOOM))
            if wx0 + ww > sw or wy0 + wh > sh:
                continue
            t = small[wy0:wy0 + wh, wx0:wx0 + ww].copy()
            t -= t.mean()
            if (t ** 2).sum() < 1e-3:
                continue
            res = ncc_full(world, t)
            idx = np.unravel_index(np.argmax(res), res.shape)
            score = float(res[idx])
            # camera implied by this patch
            camX = idx[1] - (sx0 - W / 2.0) / ZOOM
            camY = idx[0] - (sy0 - H / 2.0) / ZOOM
            est.append((score, sx0, sy0, camX, camY))
            print("   patch (%4d,%4d) ncc=%.3f -> cam=(%7.1f,%7.1f)" % (sx0, sy0, score, camX, camY))
        good = [e for e in est if e[0] > 0.55]
        if good:
            ax = np.array([[e[3], e[4]] for e in good])
            print("   %d confident patches: camX %.1f +- %.1f   camY %.1f +- %.1f"
                  % (len(good), ax[:, 0].mean(), ax[:, 0].std(), ax[:, 1].mean(), ax[:, 1].std()))
        else:
            print("   no confident patch (max ncc %.3f)" % max(e[0] for e in est))


if __name__ == "__main__":
    main()

"""Extract the diagnostic chunk borders from a captured frame.

Under the render-diagnostic toggle every visible chunk draws a 1px outline whose
colour alternates by (cx+cy) parity: cyan for even, orange for odd. Those lines
ARE the chunk dst rectangles (including the 4px bleed), so reading them out of a
screenshot recovers the dst geometry the frame actually used -- no guessing about
the camera required.

Outputs, per image:
  * every long horizontal cyan/orange line (y, x extent, colour)
  * every long vertical   cyan/orange line (x, y extent, colour)
  * an overlay PNG: detected borders in saturated blue/red on a dimmed shot
"""
import os
import numpy as np
from PIL import Image

SHOTS = r"C:\Users\XiaoXin\AppData\Local\Temp\xjzb_shots"
OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
W, H = 2608, 1200


def runs(idx, gap=2, minlen=40):
    if len(idx) == 0:
        return []
    out = []
    s = p = idx[0]
    for i in idx[1:]:
        if i > p + 1 + gap:
            if p - s + 1 >= minlen:
                out.append((int(s), int(p)))
            s = i
        p = i
    if p - s + 1 >= minlen:
        out.append((int(s), int(p)))
    return out


def main():
    for name in ("a1.jpg", "a2.jpg"):
        a = np.asarray(Image.open(os.path.join(SHOTS, name)).convert("RGB")).astype(np.int16)
        R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
        # a 1px line survives JPEG as a few pixels whose channel order is still
        # clearly separated, so a low threshold plus a long-run filter works.
        cyan = ((B - R) > 30) & ((G - R) > 25) & (B > 90)
        orng = ((R - B) > 45) & (R > 120) & (G > 70)
        print("== %s   cyan px %d   orange px %d" % (name, cyan.sum(), orng.sum()))
        for tag, m in (("CYAN", cyan), ("ORNG", orng)):
            print("  -- %s horizontal lines (row: x-extent) where row-count > 150" % tag)
            cnt = m.sum(axis=1)
            for y in np.where(cnt > 150)[0]:
                r = runs(np.where(m[y])[0])
                print("     y=%4d  n=%4d  runs=%s" % (y, cnt[y], r))
            print("  -- %s vertical lines (col: y-extent) where col-count > 150" % tag)
            cnt = m.sum(axis=0)
            for x in np.where(cnt > 150)[0]:
                r = runs(np.where(m[:, x])[0])
                print("     x=%4d  n=%4d  runs=%s" % (x, cnt[x], r))
        vis = (a // 3).astype(np.uint8)
        vis[cyan] = (0, 90, 255)
        vis[orng] = (255, 40, 0)
        green = (G > 185) & (R < 105) & (B < 105)
        vis[green] = (0, 255, 0)
        Image.fromarray(vis).save(os.path.join(OUT, "_grid_" + name.replace(".jpg", ".png")))
        print("   overlay ->", os.path.join(OUT, "_grid_" + name.replace(".jpg", ".png")))


if __name__ == "__main__":
    main()

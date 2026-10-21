import numpy as np
from PIL import Image

base = r"C:\Users\XiaoXin\AppData\Local\Temp\xjzb_shots"
for name in ["a1.jpg", "a2.jpg"]:
    a = np.array(Image.open(base + "\\" + name).convert("RGB")).astype(np.int16)
    h, w, _ = a.shape
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    print("=" * 72)
    print(name, w, "x", h)
    green = (G > 170) & (R < 110) & (B < 110) & ((G - R) > 80) & ((G - B) > 80)
    rf = green.mean(axis=1)
    rows = np.nonzero(rf > 0.02)[0]
    groups = []
    s = None
    prev = None
    for y in rows:
        if s is None:
            s = y
        elif y != prev + 1:
            groups.append((s, prev))
            s = y
        prev = y
    if s is not None:
        groups.append((s, prev))
    print(" green row groups (y0..y1 h maxfrac x0..x1):")
    for y0, y1 in groups:
        sub = green[y0:y1 + 1]
        cols = np.nonzero(sub.any(axis=0))[0]
        print("   %4d..%4d h=%3d maxfrac=%.3f x=%d..%d" %
              (y0, y1, y1 - y0 + 1, rf[y0:y1 + 1].max(), cols.min(), cols.max()))
    d = np.abs(a[1:, :, :] - a[:-1, :, :]).sum(axis=2).mean(axis=1)
    idx = np.argsort(d)[::-1][:24]
    print(" top horiz discontinuities:", sorted([(int(i), round(float(d[i]), 1)) for i in idx]))
    dc = np.abs(a[:, 1:, :] - a[:, :-1, :]).sum(axis=2).mean(axis=0)
    idxc = np.argsort(dc)[::-1][:16]
    print(" top vert  discontinuities:", sorted([(int(i), round(float(dc[i]), 1)) for i in idxc]))
    if groups:
        y0, y1 = max(groups, key=lambda g: g[1] - g[0])
        x = w // 2
        print(" vertical profile at x=%d:" % x)
        for y in range(max(0, y0 - 8), min(h, y1 + 9), 2):
            print("    y=%4d rgb=(%3d,%3d,%3d)" % (y, a[y, x, 0], a[y, x, 1], a[y, x, 2]))

# v2.43: side-by-side of the real-device report and the new previews.
# Top: the device screenshot's info card, measured 1541x137 at x680..2220.
# Below: the same region of each preview, so the widths compare directly.
from PIL import Image, ImageDraw
import os

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
dev = Image.open(os.path.join(OUT, "_scv_panel.jpg")).convert("RGB")

# device panel: x 680..2220, y 1044..1180 (measured). Take a band a little
# wider so the neighbouring widgets (group grid / command card) stay visible
# as scale references.
DEV_BOX = (300, 1020, 2608, 1200)

rows = []
rows.append(("device (before, 1541px panel)", dev.crop(DEV_BOX)))

for name, label in (("hud_v242_multi_scv.png", "after: SCV x5 (uniform, 1 kind)"),
                    ("hud_v242_multi_mixed.png", "after: 3 kinds"),
                    ("hud_v242_multi_six.png", "after: 6 kinds")):
    p = os.path.join(OUT, name)
    if os.path.exists(p):
        rows.append((label, Image.open(p).convert("RGB").crop(DEV_BOX)))

W = DEV_BOX[2] - DEV_BOX[0]
H = DEV_BOX[3] - DEV_BOX[1]
BAR = 26
canvas = Image.new("RGB", (W, (H + BAR) * len(rows)), (16, 18, 24))
d = ImageDraw.Draw(canvas)
y = 0
for label, im in rows:
    d.rectangle([0, y, W, y + BAR - 1], fill=(30, 34, 46))
    d.text((8, y + 7), label, fill=(220, 232, 250))
    canvas.paste(im, (0, y + BAR))
    # mark the panel's left edge so the alignment is obvious
    y += H + BAR

canvas.save(os.path.join(OUT, "_v242_info_compare.png"))
print("wrote _v242_info_compare.png", canvas.size)

# numeric: measure the green bar and the panel slab in each row
import numpy as np


def measure(im):
    a = np.asarray(im).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    green = (g > 170) & (r < 150) & (b < 150) & ((g - r) > 60) & ((g - b) > 60)
    # restrict to the bottom band where the info card lives
    green[: H // 2, :] = False
    ys, xs = np.nonzero(green)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(xs.max()), int(xs.max() - xs.min() + 1)


for label, im in rows:
    m = measure(im)
    print(f"{label:44s} green bar x {m[0]}..{m[1]} width {m[2]}px" if m else
          f"{label:44s} no green bar")

# Second pass: crop selection panels from the sweep3 tap series.
import os
from PIL import Image, ImageDraw

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
SRC = os.path.join(OUT, "sweep3")
BOX = (470, 930, 1010, 1160)
W, H = BOX[2] - BOX[0], BOX[3] - BOX[1]

files = sorted([f for f in os.listdir(SRC) if f.endswith(".png")],
               key=lambda n: int(os.path.splitext(n)[0][1:]))
print("frames:", len(files))
COLS = 3
rows = (len(files) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * W, rows * (H + 18)), (18, 18, 24))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    crop = Image.open(os.path.join(SRC, f)).convert("RGB").crop(BOX)
    c, r = i % COLS, i // COLS
    sheet.paste(crop, (c * W, r * (H + 18) + 18))
    d.text((c * W + 4, r * (H + 18) + 4), f, fill=(255, 210, 90))
sheet.save(os.path.join(OUT, "_e26_panels2.png"))
print("wrote", sheet.size)

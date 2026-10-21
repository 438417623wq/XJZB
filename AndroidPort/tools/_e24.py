# Batch E real-device portrait evidence: crop the selection panel out of each
# tap screenshot and stack them into one contact sheet for eyeball review.
# Panel region in the 2992x1344 device screenshot is the left block of the
# bottom HUD strip (portrait + name + hp line).
import os
from PIL import Image, ImageDraw

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
SRC = os.path.join(OUT, "sweep")
# device pixels, verified by eyeballing v212_tap_436.png (portrait at ~x300..400)
BOX = (470, 930, 1010, 1160)   # x0,y0,x1,y1
W = BOX[2] - BOX[0]
H = BOX[3] - BOX[1]

files = sorted(os.listdir(SRC), key=lambda n: int(os.path.splitext(n)[0][1:]))
files = [f for f in files if f.endswith(".png")]
print("frames:", len(files))

COLS = 3
rows = (len(files) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * W, rows * (H + 18)), (18, 18, 24))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(os.path.join(SRC, f)).convert("RGB")
    crop = im.crop(BOX)
    c, r = i % COLS, i // COLS
    sheet.paste(crop, (c * W, r * (H + 18) + 18))
    d.text((c * W + 4, r * (H + 18) + 4), f, fill=(255, 210, 90))
sheet.save(os.path.join(OUT, "_e24_panels.png"))
print("wrote", os.path.join(OUT, "_e24_panels.png"), sheet.size)

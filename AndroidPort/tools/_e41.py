# Ruler over the command card so exact device coordinates of each cell can be read.
import os
from PIL import Image, ImageDraw

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
im = Image.open(os.path.join(OUT, "_e40_build1.png")).convert("RGB")
x0, x1 = 2500, 2992
y0, y1 = 900, 1344
strip = im.crop((x0, y0, x1, y1))
Z = 2
strip = strip.resize((strip.width * Z, strip.height * Z), Image.NEAREST)
d = ImageDraw.Draw(strip)
for dev_x in range(x0, x1, 25):
    cx = (dev_x - x0) * Z
    major = (dev_x % 100 == 0)
    d.line([(cx, 0), (cx, strip.height)], fill=(255, 40, 40) if major else (90, 90, 140), width=2 if major else 1)
    if major:
        d.text((cx + 3, 3), str(dev_x), fill=(255, 235, 80))
for dev_y in range(y0, y1, 25):
    cy = (dev_y - y0) * Z
    major = (dev_y % 100 == 0)
    d.line([(0, cy), (strip.width, cy)], fill=(40, 255, 40) if major else (70, 110, 70), width=2 if major else 1)
    if major:
        d.text((3, cy + 3), str(dev_y), fill=(120, 255, 120))
strip.save(os.path.join(OUT, "_e41_card_ruler.png"))
print("wrote", strip.size, "crop", (x0, y0, x1, y1))

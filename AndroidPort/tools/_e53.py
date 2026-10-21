# Ruler over the settings sheet's bottom area to read the 返回 button's device coords.
import os
from PIL import Image, ImageDraw

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
im = Image.open(os.path.join(OUT, "_e51_state.png")).convert("RGB")
x0, x1 = 1200, 1800
y0, y1 = 1150, 1344
strip = im.crop((x0, y0, x1, y1))
Z = 2
strip = strip.resize((strip.width * Z, strip.height * Z), Image.NEAREST)
d = ImageDraw.Draw(strip)
for dev_x in range(x0, x1, 50):
    cx = (dev_x - x0) * Z
    d.line([(cx, 0), (cx, strip.height)], fill=(255, 60, 60), width=1)
    d.text((cx + 2, 2), str(dev_x), fill=(255, 235, 80))
for dev_y in range(y0, y1, 10):
    cy = (dev_y - y0) * Z
    major = (dev_y % 50 == 0)
    d.line([(0, cy), (strip.width, cy)], fill=(60, 255, 60) if major else (60, 110, 60), width=2 if major else 1)
    d.text((2, cy + 1), str(dev_y), fill=(140, 255, 140))
strip.save(os.path.join(OUT, "_e53_back_ruler.png"))
print("wrote", strip.size)

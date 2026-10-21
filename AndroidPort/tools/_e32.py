# Fine ruler over the injected-unit row so each sprite centre can be read off
# in device pixels. The row sits near device y 655 in the 2992x1344 screenshot.
import os
from PIL import Image, ImageDraw

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
im = Image.open(os.path.join(OUT, "_e31.png")).convert("RGB")
x0, x1 = 150, 1150
y0, y1 = 590, 730
strip = im.crop((x0, y0, x1, y1))
Z = 3
strip = strip.resize((strip.width * Z, strip.height * Z), Image.NEAREST)
d = ImageDraw.Draw(strip)
for dev_x in range(x0, x1, 25):
    cx = (dev_x - x0) * Z
    major = (dev_x % 100 == 0)
    d.line([(cx, 0), (cx, strip.height)], fill=(255, 40, 40) if major else (80, 80, 130), width=2 if major else 1)
    if major:
        d.text((cx + 4, 4), str(dev_x), fill=(255, 235, 80))
strip.save(os.path.join(OUT, "_e32_ruler.png"))
print("wrote", strip.size, "crop", (x0, y0, x1, y1))

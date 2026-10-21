# Measure the injected-unit row: crop the strip and overlay a device-pixel
# ruler so each sprite's exact tap coordinate can be read off.
import os
from PIL import Image, ImageDraw

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
im = Image.open(os.path.join(OUT, "v212_m01_ingame.png")).convert("RGB")
# strip covering the injected row (device px)
y0, y1 = 400, 620
strip = im.crop((150, y0, 1600, y1))
Z = 2
strip = strip.resize((strip.width * Z, strip.height * Z), Image.NEAREST)
d = ImageDraw.Draw(strip)
# vertical rules every 50 device px, labelled with the DEVICE x coordinate
for dev_x in range(150, 1600, 50):
    cx = (dev_x - 150) * Z
    major = (dev_x % 100 == 0)
    d.line([(cx, 0), (cx, strip.height)], fill=(255, 60, 60) if major else (90, 90, 140), width=2 if major else 1)
    if major:
        d.text((cx + 3, 4), str(dev_x), fill=(255, 230, 90))
strip.save(os.path.join(OUT, "_e30_ruler.png"))
print("wrote", strip.size, "strip device y", y0, y1)

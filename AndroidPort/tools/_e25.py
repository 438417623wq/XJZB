# Locate the injected portrait units on screen: crop the unit row out of the
# in-game screenshot and upscale so each sprite can be identified by eye.
import os
from PIL import Image

OUT = r"F:\KF\XJZB\AndroidPort\tools\out"
src = os.path.join(OUT, "v212_m01_ingame.png")
im = Image.open(src).convert("RGB")
print("full", im.size)
# game viewport in the 2992x1344 landscape screenshot: roughly x 162..2490, y 170..800
box = (150, 380, 1500, 780)
crop = im.crop(box)
crop = crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST)
crop.save(os.path.join(OUT, "_e25_row.png"))
print("wrote _e25_row.png", crop.size)

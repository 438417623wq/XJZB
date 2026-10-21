from PIL import Image, features
import os
print("PIL webp support:", features.check("webp"))
base = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"
for f in ["crusader/c_0_0.webp","crusader/c_11_7.webp","crusader/c_1_2.webp",
          "newgettysburg/c_11_7.webp","newgettysburg/c_7_11.webp","divide/c_0_0.webp"]:
    p = os.path.join(base, f)
    try:
        im = Image.open(p); im.load()
        print(f, "->", im.size, im.mode, os.path.getsize(p))
    except Exception as e:
        print(f, "-> EX", type(e).__name__, e)

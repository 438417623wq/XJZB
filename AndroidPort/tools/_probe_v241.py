from PIL import Image
import os
d = r"F:\KF\XJZB\AndroidPort\tools\out\_v241_webp"
for f in sorted(os.listdir(d)):
    p = os.path.join(d, f)
    try:
        im = Image.open(p); im.load()
        print("%-40s %s %s" % (f, im.size, im.mode))
    except Exception as e:
        print("%-40s EX %s" % (f, e))

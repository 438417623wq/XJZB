from PIL import Image
import os, sys
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
SPR = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
for n in ("plasma_b.webp", "plasma_r.webp"):
    p = os.path.join(SPR, n)
    before = os.path.getsize(p)
    im = Image.open(p)
    im.load()
    im.save(p, "WEBP", lossless=True, method=3)
    print("%s %d -> %d bytes  %s" % (n, before, os.path.getsize(p), im.size))

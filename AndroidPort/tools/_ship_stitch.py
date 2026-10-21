from PIL import Image
import os
a = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"
for mid, n in (("bloodbath", 4), ("divide", 4)):
    W = n*512
    out = Image.new("RGB", (W, W))
    for cy in range(n):
        for cx in range(n):
            p = os.path.join(a, mid, "c_%d_%d.webp" % (cx, cy))
            out.paste(Image.open(p).convert("RGB"), (cx*512, cy*512))
    out.save("_ship_%s.png" % mid)
    print(mid, out.size)

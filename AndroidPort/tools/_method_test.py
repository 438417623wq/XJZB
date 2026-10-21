import os, shutil
from PIL import Image
base = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"
tmp  = r"F:\KF\XJZB\AndroidPort\tools\out\_webp_method_test"
os.makedirs(tmp, exist_ok=True)
tests = ["crusader/c_11_7", "crusader/c_1_2", "newgettysburg/c_11_7", "crusader/c_0_0"]
for t in tests:
    png = os.path.join(base, t + ".png")
    if not os.path.exists(png):
        print(t, "-> NO PNG"); continue
    im = Image.open(png)
    for m in (3, 4, 6):
        out = os.path.join(tmp, t.replace("/", "__") + "_m%d.webp" % m)
        im.save(out, "WEBP", lossless=True, method=m)
        print("%-28s method=%d size=%d" % (t, m, os.path.getsize(out)))

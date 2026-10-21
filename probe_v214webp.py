from PIL import Image
import os
SPR = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
for n in ("plasma_b","dswarm_b","psistorm_b","emp_b","dweb_b"):
    for ext in (".png",".webp"):
        p = os.path.join(SPR, n+ext)
        if not os.path.exists(p): 
            print("  %-12s %-5s MISSING" % (n, ext)); continue
        im = Image.open(p)
        print("  %-12s %-5s %s mode=%s size=%d" % (n, ext, im.size, im.mode, os.path.getsize(p)))

from PIL import Image
import os
SPR = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
TMP = r"F:\KF\XJZB\AndroidPort\tools\out\wp2"
os.makedirs(TMP, exist_ok=True)
# re-encode an existing good sheet with method=6 to see if the bug is content/size
for n in ("dswarm_b","psistorm_b","emp_b"):
    im = Image.open(os.path.join(SPR,n+".webp")).convert("RGBA")
    im.save(os.path.join(TMP, n+"_m6.webp"), "WEBP", lossless=True, method=6)
    print("%s %s m6 %d bytes" % (n, im.size, os.path.getsize(os.path.join(TMP,n+"_m6.webp"))))
# plasma at reduced widths (crop columns)
im = Image.open(os.path.join(SPR,"plasma_b.webp")).convert("RGBA")
for w in (2048, 1536, 1024, 768, 512):
    c = im.crop((0,0,w,768))
    p = os.path.join(TMP, "pl_w%d_m6.webp" % w)
    c.save(p, "WEBP", lossless=True, method=6)
    print("plasma w=%d m6 %d bytes" % (w, os.path.getsize(p)))
# plasma cropped vertically
for h in (768, 512, 384, 256):
    c = im.crop((0,0,2048,h))
    p = os.path.join(TMP, "pl_h%d_m6.webp" % h)
    c.save(p, "WEBP", lossless=True, method=6)
    print("plasma h=%d m6 %d bytes" % (h, os.path.getsize(p)))

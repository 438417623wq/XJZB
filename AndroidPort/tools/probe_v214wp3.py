from PIL import Image
import os
SPR = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
TMP = r"F:\KF\XJZB\AndroidPort\tools\out\wp3"
os.makedirs(TMP, exist_ok=True)
im = Image.open(os.path.join(SPR,"plasma_b.webp")).convert("RGBA")
for m in (0,1,2,3,4,5,6):
    p = os.path.join(TMP, "m%d.webp" % m)
    im.save(p, "WEBP", lossless=True, method=m)
    print("method=%d %d bytes" % (m, os.path.getsize(p)))
# also: does the exact same content at exact_=False help?
im.save(os.path.join(TMP,"m6_exact0.webp"), "WEBP", lossless=True, method=6, exact=False)
print("m6 exact=False", os.path.getsize(os.path.join(TMP,"m6_exact0.webp")))

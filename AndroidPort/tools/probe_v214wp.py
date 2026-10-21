from PIL import Image
import os
SPR = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
TMP = r"F:\KF\XJZB\AndroidPort\tools\out\wp"
os.makedirs(TMP, exist_ok=True)
src = os.path.join(SPR, "plasma_b.webp")
im = Image.open(src).convert("RGBA")
print("src", im.size, im.mode)
# how much of it is actually opaque?
alpha = im.getchannel("A")
bbox = alpha.getbbox()
print("alpha bbox", bbox)
# variant A: lossless method=4
im.save(os.path.join(TMP,"a_m4.webp"), "WEBP", lossless=True, method=4)
# variant B: lossless method=0
im.save(os.path.join(TMP,"b_m0.webp"), "WEBP", lossless=True, method=0)
# variant C: lossy q=95
im.save(os.path.join(TMP,"c_q95.webp"), "WEBP", quality=95)
# variant D: PNG
im.save(os.path.join(TMP,"d.png"))
# variant E: crop to content, pad to same grid
for f in sorted(os.listdir(TMP)):
    print("  %-14s %d bytes" % (f, os.path.getsize(os.path.join(TMP,f))))

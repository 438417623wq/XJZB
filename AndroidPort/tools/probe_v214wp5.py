from PIL import Image
import os
SPR = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
TMP = r"F:\KF\XJZB\AndroidPort\tools\out\wp5"
os.makedirs(TMP, exist_ok=True)
for f in sorted(os.listdir(SPR)):
    if not f.endswith(".webp"): continue
    im = Image.open(os.path.join(SPR,f))
    if im.mode not in ("RGBA","RGB"): im = im.convert("RGBA")
    im.save(os.path.join(TMP,f), "WEBP", lossless=True, method=3)
print("re-encoded", len(os.listdir(TMP)), "with method=3")

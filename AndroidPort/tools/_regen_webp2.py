import os, shutil
from PIL import Image
TMP = r"F:\KF\XJZB\AndroidPort\tools\out\_regen"
W = r"F:\KF\XJZB\AndroidPort\tools\out\_regen_webp"
if os.path.isdir(W): shutil.rmtree(W)
os.makedirs(W)
for f in sorted(os.listdir(TMP)):
    if f.endswith(".png"):
        Image.open(os.path.join(TMP, f)).convert("RGBA").save(
            os.path.join(W, f[:-4] + ".webp"), "WEBP", lossless=True, method=3)
print("webp:", len(os.listdir(W)))
for k in ["ic_controlt","ic_physicslab","ic_machineshop","ic_nukesilo","ic_scan","ic_nukestrike"]:
    im = Image.open(os.path.join(TMP, k + ".png")).convert("RGBA")
    a = im.split()[3]
    op = sum(1 for v in a.getdata() if v > 0)
    print("  %-16s %s opaque=%d" % (k, "%dx%d" % im.size, op))

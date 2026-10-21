import os, shutil
from PIL import Image
TMP = r"F:\KF\XJZB\AndroidPort\tools\out\_regen"
W = r"F:\KF\XJZB\AndroidPort\tools\out\_regen_webp"
if os.path.isdir(W): shutil.rmtree(W)
os.makedirs(W)
new = []
for f in sorted(os.listdir(TMP)):
    if not f.endswith(".png"): continue
    im = Image.open(os.path.join(TMP, f)).convert("RGBA")
    out = os.path.join(W, f[:-4] + ".webp")
    im.save(out, "WEBP", lossless=True, method=3)
    # opacity census: a sheet that decoded to nothing would be fully transparent
    a = im.split()[3]
    op = sum(1 for v in a.getdata() if v > 0)
    if f.split("_")[0] in ("comsat","controlt","machineshop","physicslab","nukesilo",
                            "nukehit","nukebeam","nuketarg","ic"):
        pass
print("webp written", len(os.listdir(W)))
for k in ["comsat_b","controlt_b","machineshop_b","physicslab_b","nukesilo_b",
          "nukehit_b","nukebeam_b","nuketarg_b","ic_scan","ic_nukestrike"]:
    p = os.path.join(TMP, k + ".png")
    im = Image.open(p).convert("RGBA")
    op = sum(1 for v in im.split()[3].getdata() if v > 0)
    print("  %-14s %-10s opaque=%d/%d" % (k, "%dx%d" % im.size, op, im.width*im.height))

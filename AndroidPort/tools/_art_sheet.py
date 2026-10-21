import os
from PIL import Image
R = r"F:\KF\XJZB\AndroidPort\tools\out\_regen"
keys = ["comsat_b", "controlt_b", "machineshop_b", "physicslab_b", "nukesilo_b",
        "nukehit_b", "nukebeam_b", "nuketarg_b", "ic_scan", "ic_nukestrike"]
ims = []
for k in keys:
    p = os.path.join(R, k + ".png")
    if os.path.exists(p):
        ims.append((k, Image.open(p).convert("RGBA")))
    else:
        print("missing", k)
maxh = max(i.height for _, i in ims)
W = sum(i.width for _, i in ims) + 12 * len(ims)
sheet = Image.new("RGB", (W, maxh + 12), (48, 48, 56))
x = 6
for k, im in ims:
    sheet.paste(im, (x, 6), im)
    x += im.width + 12
sheet.save(r"F:\KF\XJZB\AndroidPort\tools\out\_v225_art.png")
print("saved _v225_art.png", sheet.size, [k for k, _ in ims])

import zipfile, io, json, os
import numpy as np
from PIL import Image
A = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk"
B = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.42.apk"
za, zb = zipfile.ZipFile(A), zipfile.ZipFile(B)
# 1) minimap pixel identity
mm_same = mm_diff = 0
for n in za.namelist():
    if not n.endswith("/minimap.webp"): continue
    if n not in zb.namelist(): continue
    a = np.asarray(Image.open(io.BytesIO(za.read(n))).convert("RGB"))
    b = np.asarray(Image.open(io.BytesIO(zb.read(n))).convert("RGB"))
    if a.shape == b.shape and np.array_equal(a, b): mm_same += 1
    else: mm_diff += 1
print("minimap pixel-identical=%d diff=%d" % (mm_same, mm_diff))
# 2) meta.json diff sample
shown = 0
for n in sorted(za.namelist()):
    if not n.endswith("/meta.json"): continue
    if n not in zb.namelist(): continue
    a, b = za.read(n), zb.read(n)
    if a == b: continue
    if shown < 3:
        ja, jb = json.loads(a), json.loads(b)
        ka = set(ja); kb = set(jb)
        print("==", n)
        print("   v241 keys:", sorted(ka))
        print("   v242 keys:", sorted(kb))
        for k in sorted(ka & kb):
            if ja[k] != jb[k]:
                print("   ~ %s: %r -> %r" % (k, ja[k], jb[k]))
        shown += 1
# 3) walk.bin
for n in za.namelist():
    if n.endswith("/walk.bin") and n in zb.namelist() and za.read(n) != zb.read(n):
        print("walk.bin changed:", n, len(za.read(n)), len(zb.read(n)))

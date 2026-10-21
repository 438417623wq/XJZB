import zipfile, io, os
import numpy as np
from PIL import Image
A = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk"
B = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.42.apk"
za, zb = zipfile.ZipFile(A), zipfile.ZipFile(B)
rows = []
for n in za.namelist():
    if not n.endswith("/minimap.webp"): continue
    if n not in zb.namelist(): continue
    a = np.asarray(Image.open(io.BytesIO(za.read(n))).convert("RGB")).astype(np.int16)
    b = np.asarray(Image.open(io.BytesIO(zb.read(n))).convert("RGB")).astype(np.int16)
    if a.shape != b.shape:
        rows.append((n.split("/")[-2], -1, -1, "SHAPE")); continue
    d = np.abs(a - b).max(axis=2)
    npx = int((d > 0).sum())
    big = int((d > 40).sum())
    rows.append((n.split("/")[-2], npx, big, a.shape))
rows.sort(key=lambda r: -r[1])
print("%-18s %8s %8s  shape" % ("map", "diffpx", ">40"))
for m, npx, big, sh in rows:
    if npx: print("%-18s %8d %8d  %s" % (m, npx, big, sh))
print("total maps with minimap change: %d / %d" % (sum(1 for r in rows if r[1] > 0), len(rows)))

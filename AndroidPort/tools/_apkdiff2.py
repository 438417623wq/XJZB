import zipfile, hashlib, os
import numpy as np
from PIL import Image
import io
A = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk"
B = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.42.apk"
za, zb = zipfile.ZipFile(A), zipfile.ZipFile(B)
na = {i.filename: i for i in za.infolist()}
nb = {i.filename: i for i in zb.infolist()}
common = sorted(set(na) & set(nb))
cats = {}
chunk_byte_same = chunk_byte_diff_pix_same = chunk_pix_diff = 0
for n in common:
    if na[n].file_size != nb[n].file_size or hashlib.sha256(za.read(n)).hexdigest() != hashlib.sha256(zb.read(n)).hexdigest():
        base = os.path.basename(n)
        if n.startswith("assets/maps/") and base.startswith("c_") and base.endswith(".webp"):
            a = np.asarray(Image.open(io.BytesIO(za.read(n))).convert("RGB"))
            b = np.asarray(Image.open(io.BytesIO(zb.read(n))).convert("RGB"))
            if a.shape == b.shape and np.array_equal(a, b):
                chunk_byte_diff_pix_same += 1
            else:
                chunk_pix_diff += 1
        else:
            key = os.path.basename(n) if n.startswith("assets/maps/") else n
            if n.startswith("assets/maps/"):
                key = n.split("/")[-1]
            cats[key] = cats.get(key, 0) + 1
print("chunks: byte-diff but pixel-IDENTICAL =", chunk_byte_diff_pix_same)
print("chunks: pixel-diff =", chunk_pix_diff)
print("--- other changed entries by filename ---")
for k in sorted(cats, key=lambda k: -cats[k]):
    print("   %-24s %d" % (k, cats[k]))

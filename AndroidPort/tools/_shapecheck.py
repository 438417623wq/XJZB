import io, os, zipfile
import numpy as np
from PIL import Image
APK = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk"
DISK = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"
z = zipfile.ZipFile(APK)
shapes = {}
bad = []
for name in z.namelist():
    if not (name.startswith("assets/maps/") and name.endswith(".webp")): continue
    if not os.path.basename(name).startswith("c_"): continue
    mid = name.split("/")[2]; fn = name.split("/")[-1]
    disk = os.path.join(DISK, mid, fn)
    if not os.path.exists(disk): bad.append("MISSING "+mid+"/"+fn); continue
    a = Image.open(io.BytesIO(z.read(name))); b = Image.open(disk)
    shapes[a.size] = shapes.get(a.size, 0) + 1
    if a.size != b.size: bad.append("SIZE %s/%s %s vs %s" % (mid, fn, a.size, b.size))
print("v2.41 chunk sizes:", shapes)
print("anomalies:", len(bad))
for x in bad[:20]: print("  ", x)

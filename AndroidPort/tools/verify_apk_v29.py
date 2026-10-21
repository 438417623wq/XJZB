"""Byte-compare APK assets vs disk (the project's standard release audit),
then print the sunken sheet hash on both sides.

One wrinkle: AGP's mergeReleaseAssets transparently gunzips any ".gz" asset and
drops the extension. tools/slim_assets.py ships maps/<id>/walk.bin.gz, so the
APK legitimately contains maps/<id>/walk.bin holding the *decompressed* bytes.
Counting those as "only in APK / only on disk" would report a 9-file false
alarm, so the disk side is gunzipped and re-keyed before comparing.
"""
import gzip
import hashlib
import os
import zipfile

APK = r"F:\KF\XJZB\AndroidPort\app\app\build\outputs\apk\release\app-release.apk"
DISK = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"

z = zipfile.ZipFile(APK)
apk_files = {}
for n in z.namelist():
    if n.startswith("assets/"):
        apk_files[n[len("assets/"):]] = z.read(n)

disk_files = {}
for root, _dirs, files in os.walk(DISK):
    for f in files:
        p = os.path.join(root, f)
        rel = os.path.relpath(p, DISK).replace("\\", "/")
        data = open(p, "rb").read()
        if rel.endswith(".gz"):
            # AGP will decompress this and strip the suffix; mirror that here.
            rel = rel[:-3]
            data = gzip.decompress(data)
        disk_files[rel] = data

same = diff = only_apk = only_disk = 0
for k, v in apk_files.items():
    if k not in disk_files:
        only_apk += 1
        print("  only in APK:", k, len(v))
    elif v == disk_files[k]:
        same += 1
    else:
        diff += 1
        print("  DIFF:", k, len(v), "vs", len(disk_files[k]))
for k in disk_files:
    if k not in apk_files:
        only_disk += 1
        print("  only on disk:", k, len(disk_files[k]))
print("same=%d diff=%d only_apk=%d only_disk=%d" % (same, diff, only_apk, only_disk))

for k in ("sprites/sunken_b.webp", "sprites/sunken_r.webp"):
    h1 = hashlib.sha256(apk_files[k]).hexdigest()[:16]
    h2 = hashlib.sha256(disk_files[k]).hexdigest()[:16]
    print(k, "apk", h1, "disk", h2, "match" if h1 == h2 else "DIFF")

print("GATE:", "PASS" if (diff == 0 and only_apk == 0 and only_disk == 0) else "FAIL")

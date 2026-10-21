import zipfile, os
A = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk"
DISK = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
za = zipfile.ZipFile(A)
same = diff = miss = 0
diffs = []
for n in za.namelist():
    if not (n.endswith("/meta.json") or n.endswith("/meta.txt") or n.endswith("/index.txt")):
        continue
    rel = n[len("assets/"):] if n.startswith("assets/") else n
    p = os.path.join(DISK, rel.replace("/", os.sep))
    if not os.path.exists(p):
        miss += 1; diffs.append("MISS " + n); continue
    if za.read(n) == open(p, "rb").read():
        same += 1
    else:
        diff += 1; diffs.append("DIFF " + n)
print("meta.json/meta.txt/index.txt vs v2.41 APK: same=%d diff=%d missing=%d" % (same, diff, miss))
for d in diffs[:15]: print("  ", d)

import zipfile, os
A = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk"
DISK = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
za = zipfile.ZipFile(A)
for kind in ("/meta.txt", "/index.txt"):
    same = diff = miss = 0
    for n in za.namelist():
        if not n.endswith(kind): continue
        rel = n[len("assets/"):]
        p = os.path.join(DISK, rel.replace("/", os.sep))
        if not os.path.exists(p): miss += 1; continue
        if za.read(n) == open(p, "rb").read(): same += 1
        else: diff += 1; print("  DIFF", n)
    print("%-12s same=%d diff=%d missing=%d" % (kind, same, diff, miss))

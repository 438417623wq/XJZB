import zipfile, os
A = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk"
DISK = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
za = zipfile.ZipFile(A)
for mid in ("bloodbath", "divide", "darkcrystal"):
    n = "assets/maps/%s/walk.bin" % mid
    if n not in za.namelist(): print(mid, "absent in apk"); continue
    a = za.read(n)
    p = os.path.join(DISK, "maps", mid, "walk.bin")
    if not os.path.exists(p):
        p = os.path.join(DISK, "maps", mid, "walk.bin.gz")
        import gzip
        b = gzip.open(p, "rb").read()
    else:
        b = open(p, "rb").read()
    diff = sum(1 for i in range(min(len(a), len(b))) if a[i] != b[i])
    print("%-12s len %d vs %d  differing bytes=%d" % (mid, len(a), len(b), diff))

import zipfile, os
apk = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk"
outdir = r"F:\KF\XJZB\AndroidPort\tools\out\_v241_webp"
os.makedirs(outdir, exist_ok=True)
want = ["crusader/c_11_7.webp","crusader/c_1_2.webp","crusader/c_0_0.webp",
        "newgettysburg/c_11_7.webp","divide/c_0_0.webp","3kingdoms/c_0_0.webp"]
z = zipfile.ZipFile(apk)
names = set(z.namelist())
for w in want:
    n = "assets/maps/" + w
    if n not in names:
        print("MISSING in apk:", n); continue
    data = z.read(n)
    dst = os.path.join(outdir, w.replace("/", "__"))
    open(dst, "wb").write(data)
    print("%-34s apk=%7d" % (w, len(data)))

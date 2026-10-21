import zipfile, os
A = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk"
DISK = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets"
za = zipfile.ZipFile(A)
a = za.read("assets/maps/divide/meta.json")
b = open(os.path.join(DISK, "maps", "divide", "meta.json"), "rb").read()
for i in range(min(len(a), len(b))):
    if a[i] != b[i]:
        print("first diff at byte", i)
        print("  v241:", a[max(0,i-60):i+60])
        print("  v242:", b[max(0,i-60):i+60])
        break
else:
    print("no differing byte in common prefix; len %d vs %d" % (len(a), len(b)))

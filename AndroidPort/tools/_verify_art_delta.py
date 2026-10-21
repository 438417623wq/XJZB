import os, zipfile, hashlib
SPR = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
APK = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.24.apk"
def h(b): return hashlib.sha256(b).hexdigest()
z = zipfile.ZipFile(APK)
apk = {n.split("/")[-1]: z.read(n) for n in z.namelist() if n.startswith("assets/sprites/")}
disk = {}
for f in os.listdir(SPR):
    p = os.path.join(SPR, f)
    if os.path.isfile(p):
        disk[f] = open(p, "rb").read()
only_disk = sorted(set(disk) - set(apk))
only_apk = sorted(set(apk) - set(disk))
diff = sorted(k for k in disk if k in apk and disk[k] != apk[k])
print("disk=%d apk=%d" % (len(disk), len(apk)))
print("only_disk (%d): %s" % (len(only_disk), only_disk))
print("only_apk  (%d): %s" % (len(only_apk), only_apk))
print("diff (%d): %s" % (len(diff), diff))
z.close()

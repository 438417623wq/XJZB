import os, zipfile, hashlib
SPR = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
APK = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.24.apk"
NEW = set(["comsat_b.webp","comsat_r.webp","controlt_b.webp","controlt_r.webp",
           "ic_nukestrike.webp","ic_scan.webp","machineshop_b.webp","machineshop_r.webp",
           "nukebeam_b.webp","nukebeam_r.webp","nukehit_b.webp","nukehit_r.webp",
           "nukesilo_b.webp","nukesilo_r.webp","nuketarg_b.webp","nuketarg_r.webp",
           "physicslab_b.webp","physicslab_r.webp"])
def h(p): return hashlib.sha256(open(p,"rb").read()).hexdigest()
z = zipfile.ZipFile(APK)
restored = 0
for f in sorted(os.listdir(SPR)):
    if f in NEW or not f.endswith(".webp"):
        continue
    name = "assets/sprites/" + f
    try:
        data = z.read(name)
    except KeyError:
        continue
    p = os.path.join(SPR, f)
    if open(p, "rb").read() != data:
        open(p, "wb").write(data)
        restored += 1
z.close()
print("restored %d sheets to their exact v2.24 bytes" % restored)

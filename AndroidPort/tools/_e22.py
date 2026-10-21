import zipfile
APK=r"F:\KF\XJZB\AndroidPort\app\app\build\outputs\apk\release\app-release.apk"
z=zipfile.ZipFile(APK)
names=z.namelist()
print("APK entries:", len(names))
print("--- portraits in APK ---")
for n in sorted(names):
    if "portrait/" in n: print("  %-46s %d" % (n, z.getinfo(n).file_size))
print("--- ui_* sounds in APK ---")
for n in sorted(names):
    if n.startswith("assets/sounds/ui_"): print("  %-46s %d" % (n, z.getinfo(n).file_size))

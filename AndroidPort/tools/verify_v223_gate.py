"""v2.23 asset gate: byte-compare v2.22 vs v2.23 APK assets, classifying the
intended metadata changes separately from the art.

Art (.webp/.png) must be byte-identical except for the genuinely new sheets;
the only allowed drift is meta.txt/meta.json/index.txt (the elev=/island=
flags) and the sprite manifest (two new rows).
"""
import hashlib, zipfile

OLD = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.22.apk"
NEW = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.23.apk"

def read(path):
    z = zipfile.ZipFile(path)
    out = {}
    for n in z.namelist():
        if n.startswith("assets/") and not n.endswith("/"):
            out[n[len("assets/"):]] = hashlib.sha256(z.read(n)).hexdigest()
    return out

a, b = read(OLD), read(NEW)
same = only_new = only_old = 0
art_diff = []
meta_diff = []
new_files = []
for k, v in b.items():
    if k not in a:
        only_new += 1
        new_files.append(k)
    elif a[k] == v:
        same += 1
    elif k.endswith((".webp", ".png")):
        art_diff.append(k)
    else:
        meta_diff.append(k)
for k in a:
    if k not in b:
        only_old += 1

print("old=%d new=%d same=%d only_new=%d only_old=%d" % (len(a), len(b), same, only_new, only_old))
print("art files changed: %d %s" % (len(art_diff), art_diff[:10]))
print("metadata files changed: %d" % len(meta_diff))
for k in sorted(meta_diff):
    print("   ", k)
print("new files: %d" % only_new)
nonart_new = [k for k in new_files if not k.endswith((".webp", ".png", ".bin"))]
print("new non-art:", sorted(nonart_new)[:20])
print("new art:", sorted(k for k in new_files if k.endswith((".webp", ".png"))))
print("new bin:", len([k for k in new_files if k.endswith(".bin")]))
print("GATE:", "PASS" if not art_diff and only_old == 0 else "FAIL")

import os, shutil, hashlib
SPR = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
W = r"F:\KF\XJZB\AndroidPort\tools\out\_regen_webp"
TMP = r"F:\KF\XJZB\AndroidPort\tools\out\_regen"
def h(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
added, replaced, unchanged = [], [], 0
for f in sorted(os.listdir(W)):
    src = os.path.join(W, f)
    dst = os.path.join(SPR, f)
    if not os.path.exists(dst):
        shutil.copy2(src, dst); added.append(f)
    elif h(src) != h(dst):
        shutil.copy2(src, dst); replaced.append(f)
    else:
        unchanged += 1
for name in ("manifest.txt", "manifest.json"):
    shutil.copy2(os.path.join(TMP, name), os.path.join(SPR, name))
print("added=%d replaced=%d unchanged=%d" % (len(added), len(replaced), unchanged))
print("added:", added)
print("replaced:", replaced)

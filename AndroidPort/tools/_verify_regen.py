"""Webp-ify the temp regen (same settings as slim_assets) and diff vs shipped."""
import os, hashlib
from PIL import Image
TMP = r"F:\KF\XJZB\AndroidPort\tools\out\_regen"
W = r"F:\KF\XJZB\AndroidPort\tools\out\_regen_webp"
os.makedirs(W, exist_ok=True)
for f in os.listdir(TMP):
    if f.endswith(".png"):
        Image.open(os.path.join(TMP, f)).save(os.path.join(W, f[:-4] + ".webp"),
                                              "WEBP", lossless=True, method=3)
A = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
def h(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
shipped = {f: h(os.path.join(A, f)) for f in os.listdir(A) if os.path.isfile(os.path.join(A, f))}
regen = {f: h(os.path.join(W, f)) for f in os.listdir(W)}
same = [k for k in regen if k in shipped and shipped[k] == regen[k]]
diff = [k for k in regen if k in shipped and shipped[k] != regen[k]]
only_ship = sorted(set(shipped) - set(regen))
only_regen = sorted(set(regen) - set(shipped))
print("regen=%d shipped=%d same=%d diff=%d only_ship=%d only_regen=%d"
      % (len(regen), len(shipped), len(same), len(diff), len(only_ship), len(only_regen)))
print("diff:", diff[:20])
print("only_ship:", only_ship[:20])
print("only_regen:", only_regen[:20])

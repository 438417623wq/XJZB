import os, hashlib
A = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
B = r"F:\KF\XJZB\AndroidPort\tools\out\_regen"
def h(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()
def tree(d):
    out = {}
    for f in os.listdir(d):
        p = os.path.join(d, f)
        if os.path.isfile(p):
            out[f] = h(p)
    return out
a, b = tree(A), tree(B)
same = diff = only_a = only_b = 0
diffs = []
for k, v in a.items():
    if k not in b: only_a += 1; diffs.append("ONLY_SHIPPED " + k)
    elif v == b[k]: same += 1
    else: diff += 1; diffs.append("DIFF " + k)
for k in b:
    if k not in a: only_b += 1; diffs.append("ONLY_REGEN " + k)
print("shipped=%d regen=%d same=%d diff=%d only_shipped=%d only_regen=%d" % (len(a), len(b), same, diff, only_a, only_b))
for d in diffs[:40]:
    print("  " + d)

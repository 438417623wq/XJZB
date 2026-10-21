import difflib, os
A = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites\manifest.txt"
B = r"F:\KF\XJZB\AndroidPort\tools\out\_regen\manifest.txt"
a = open(A, encoding="utf8").read().splitlines()
b = open(B, encoding="utf8").read().splitlines()
print("shipped rows=%d  regen rows=%d" % (len(a), len(b)))
sa, sb = set(a), set(b)
only_b = [r for r in b if r not in sa]
missing = [r for r in a if r not in sb]
print("new rows (%d):" % len(only_b))
for r in only_b: print("   +", r)
print("missing rows (%d):" % len(missing))
for r in missing: print("   -", r)
# ordering: are the first len(a) rows identical?
print("prefix identical:", a == b[:len(a)])

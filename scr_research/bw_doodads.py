import sys, os, re, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
T = r"F:\KF\XJZB\AndroidPort\tools"
lf = os.path.join(T, "listfile_BrooDat.txt")
names = open(lf, encoding="utf-8", errors="replace").read().splitlines()
per = collections.Counter()
for n in names:
    low = n.lower()
    m = re.match(r"unit\\thingy\\tileset\\([^\\]+)\\.+\.[a-z]+$", low)
    if m:
        per[m.group(1)] += 1
print("listfile BrooDat unit\\thingy\\tileset\\<ts>\\ files:", dict(per), "sum", sum(per.values()))
for t in ("desert","ice","twilight"):
    hits = sorted(x for x in names if f"tileset\\{t}\\" in x.lower())
    print(f"  {t}: {len(hits)} -> {[os.path.basename(x) for x in hits][:20]}")

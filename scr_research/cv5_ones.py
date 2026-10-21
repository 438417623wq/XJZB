import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
d = r"F:\KF\XJZB\scr_research\tileset"
TS = ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]
for t in TS:
    b = open(os.path.join(d, f"{t}.cv5"), "rb").read()
    n = len(b)//52
    c = collections.Counter(struct.unpack_from("<H", b, g*52)[0] for g in range(n))
    ones = [g for g in range(n) if struct.unpack_from("<H", b, g*52)[0] == 1]
    print(f"{t:10s} n={n:5d} type1groups={len(ones):4d} top5={c.most_common(5)}")
print()
b = open(os.path.join(d, "twilight.cv5"), "rb").read()
for g in [g for g in range(len(b)//52) if struct.unpack_from("<H", b, g*52)[0] == 1]:
    print(f"twilight group {g}: {b[g*52:g*52+52].hex(' ')}")

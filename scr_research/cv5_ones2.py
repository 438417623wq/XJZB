import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = r"F:\KF\XJZB\scr_research\tileset"
for ts in ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]:
    b = open(os.path.join(D, ts + ".cv5"),"rb").read()
    n = len(b)//52
    c0 = collections.Counter(struct.unpack_from("<H", b, g*52)[0] for g in range(n))
    ones = [g for g in range(n) if struct.unpack_from("<H", b, g*52)[0] == 1]
    print(f"{ts:9s} n={n:5d} off0==1 count={len(ones)} first10={ones[:10]} off0 distinct={sorted(c0)[:25]}")

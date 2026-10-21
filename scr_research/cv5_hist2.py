import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = r"F:\KF\XJZB\scr_research\tileset"
for ts in ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]:
    p = os.path.join(D, ts + ".cv5")
    b = open(p,"rb").read()
    n = len(b)//52
    hist = collections.Counter()
    names_nonzero = 0
    for g in range(n):
        at = g*52
        v0 = struct.unpack_from("<H", b, at)[0]
        hist[v0] += 1
        nm = struct.unpack_from("<H", b, at+8)[0]
        if nm: names_nonzero += 1
    top = hist.most_common(6)
    print(f"{ts:9s} groups={n:5d}  u16[0] hist top6={top}  doodadName!=0 count={names_nonzero}")

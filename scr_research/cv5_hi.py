import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = r"F:\KF\XJZB\scr_research\tileset"
for ts in ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]:
    b = open(os.path.join(D, ts + ".cv5"),"rb").read()
    n = len(b)//52
    # histogram of offset0 in the 1024+ range
    c = collections.Counter()
    for g in range(1024, n):
        c[struct.unpack_from("<H", b, g*52)[0]] += 1
    print(f"{ts:9s} groups={n:5d}  offset0 hist(1024+)={dict(list(c.most_common(6)))}")
    for g in (1024, 1025, 1026, 1027):
        if g < n:
            u = struct.unpack_from("<10H", b, g*52)
            print(f"    g{g} u16[0..9]={u}")

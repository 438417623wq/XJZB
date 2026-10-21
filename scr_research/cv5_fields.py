import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = r"F:\KF\XJZB\scr_research\tileset"
for ts in ["badlands","platform"]:
    b = open(os.path.join(D, ts + ".cv5"),"rb").read()
    n = len(b)//52
    print("=====", ts, "groups", n)
    for off in range(0, 20, 2):
        c = collections.Counter(struct.unpack_from("<H", b, g*52+off)[0] for g in range(n))
        nz = sum(v for k,v in c.items() if k != 0)
        print(f"  off{off:2d}: nonzero={nz:5d} distinct={len(c):5d} top6={c.most_common(6)}")

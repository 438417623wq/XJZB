import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = r"F:\KF\XJZB\scr_research\tileset"
for ts in ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]:
    b = open(os.path.join(D, ts + ".cv5"),"rb").read()
    n = len(b)//52
    ones = [g for g in range(n) if struct.unpack_from("<H", b, g*52)[0] == 1]
    print(f"{ts:9s} n={n:5d} offset0==1 count={len(ones):4d} first20={ones[:20]}")
    # doodad-looking: offset0==1 and flags has 0x1000/0x2000
    dd = [g for g in ones if struct.unpack_from("<H", b, g*52+2)[0] & 0x3000]
    print(f"           of those, flags&0x3000={len(dd)} first10={dd[:10]}")

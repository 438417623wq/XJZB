import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = r"F:\KF\XJZB\scr_research\tileset"
for ts in ["badlands","platform","install","ashworld","jungle"]:
    b = open(os.path.join(D, ts + ".cv5"),"rb").read()
    n = len(b)//52
    ov = [g for g in range(n) if struct.unpack_from("<H", b, g*52+2)[0] & 0x3000]
    print(f"=== {ts}: groups={n}  flags&0x3000 groups={len(ov)} first15={ov[:15]}")
    for g in ov[:6]:
        u = struct.unpack_from("<10H", b, g*52)
        print(f"    g{g:5d} u16[0..9]={u}  tiles[0..3]={struct.unpack_from('<4H', b, g*52+20)}")

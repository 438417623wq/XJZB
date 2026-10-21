import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = r"F:\KF\XJZB\scr_research\tileset"
for ts in ["badlands","platform","install"]:
    b = open(os.path.join(D, ts + ".cv5"),"rb").read()
    print("=====", ts, len(b))
    for g in range(4):
        rec = b[g*52:(g+1)*52]
        print(f" g{g}: {rec.hex(' ')}")
        print(f"      u16: {struct.unpack('<26H', rec)}")

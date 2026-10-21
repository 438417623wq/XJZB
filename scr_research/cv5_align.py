import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = r"F:\KF\XJZB\scr_research\tileset"
for ts in ["badlands","platform","jungle","ashworld"]:
    b = open(os.path.join(D, ts + ".cv5"),"rb").read()
    n = len(b)//52
    print("="*15, ts, "groups", n)
    for g in (1024, 1025, 1026, 1027, 1500 if n>1500 else 1024):
        if g >= n: continue
        u = struct.unpack_from("<26H", b, g*52)
        print(f"  g{g}: idx={u[0]} flags={u[1]} edges={u[2:6]} stack={u[6:10]} tiles={u[10:26]}")
    # alignment scan: base offset that maximises count of u16==1 at 52 stride
    best = []
    for base in range(0, 52, 2):
        c = 0
        g = 1024
        while base + g*52 + 2 <= len(b):
            if struct.unpack_from("<H", b, base + g*52)[0] == 1: c += 1
            g += 1
        best.append((c, base))
    best.sort(reverse=True)
    print("  alignment scan (count of idx==1 in 1024+, top3):", best[:3])

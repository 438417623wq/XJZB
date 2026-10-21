import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = r"F:\KF\XJZB\scr_research\tileset"
def scan(ts, stride=52):
    b = open(os.path.join(D, ts + ".cv5"),"rb").read()
    n = len(b)//stride
    best = []
    for s in range(0, stride-18, 2):
        cnt = 0
        for g in range(n):
            at = g*stride + s
            if at+18 > len(b): break
            idx, fl, ov, rem, nm, unk, dd, w, h = struct.unpack_from("<9H", b, at)
            if idx == 1 and 0 < w <= 16 and 0 < h <= 16 and dd < 512 and nm != 0:
                cnt += 1
        best.append((cnt, s))
    best.sort(reverse=True)
    return n, best[:6]
for ts in ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]:
    n, best = scan(ts)
    print(f"{ts:9s} n={n:5d} best shifts {best}")

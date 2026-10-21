import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = r"F:\KF\XJZB\scr_research\tileset"
for ts in ["badlands","platform","jungle"]:
    b = open(os.path.join(D, ts + ".cv5"),"rb").read()
    n = len(b)//52
    print("=====", ts, "groups", n)
    # alignment test: for each shift, count groups whose u16 at that shift == 1
    for s in range(0, 52, 2):
        cnt = sum(1 for g in range(n) if g*52+s+2 <= len(b) and struct.unpack_from("<H", b, g*52+s)[0] == 1)
        if cnt > 3:
            print(f"   shift {s:2d}: u16==1 in {cnt} groups")
    # also: where are the 01 00 byte pairs relative to 52 grid
    al = collections.Counter()
    i = b.find(b"\x01\x00")
    while i >= 0:
        al[i % 52] += 1
        i = b.find(b"\x01\x00", i+1)
    print("   01 00 alignment histogram (mod 52):", sorted(al.items(), key=lambda x:-x[1])[:8])

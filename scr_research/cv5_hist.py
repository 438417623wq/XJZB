import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
d = r"F:\KF\XJZB\scr_research\tileset"
for t in ["badlands","platform","ashworld","install"]:
    b = open(os.path.join(d, f"{t}.cv5"), "rb").read()
    n = len(b)//52
    c0 = collections.Counter(struct.unpack_from("<H", b, g*52)[0] for g in range(n))
    print(f"--- {t} n={n} top offset0 values: {c0.most_common(8)}")
    # show first 3 records as hex
    for g in range(3):
        print("   rec%d: %s" % (g, b[g*52:g*52+52].hex(" ")))
    # find any record whose offset0 == 1
    hits = [g for g in range(n) if struct.unpack_from("<H", b, g*52)[0] == 1]
    print(f"   offset0==1 count={len(hits)} first={hits[:10]}")
    # distribution of offset2 flags
    c2 = collections.Counter(struct.unpack_from("<H", b, g*52+2)[0] for g in range(n))
    print(f"   offset2 top: {c2.most_common(6)}")

import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
d = r"F:\KF\XJZB\scr_research\tileset"
TS = ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]
tab = {}
for t in TS:
    b = open(os.path.join(d, f"{t}.dddata.bin"), "rb").read()
    tab[t] = {e for e in range(512) if any(struct.unpack_from("<256H", b, e*512))}
print(f"{'id':>5s} " + " ".join(f"{t[:6]:>7s}" for t in TS))
for i in [0,1,137,138,139,140,141,142,256,257,258,287,394,403,511]:
    row = " ".join(f"{'yes' if i in tab[t] else '.':>7s}" for t in TS)
    print(f"{i:5d} {row}")
print()
print("union of all tilesets:", len(set().union(*tab.values())), "max id in union:", max(set().union(*tab.values())))
print("per-tileset table id-space size: 512 (0..511) in every tileset")

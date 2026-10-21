import os, sys, glob, re, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
TILESET = {0:"badlands",1:"platform",2:"install",3:"ashworld",4:"jungle"}

cands = sorted(glob.glob(r"F:\KF\XJZB\maps\**\*.sc*", recursive=True))
rows = []
for p in cands:
    r = pm.read_chk(p)
    if not r: continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    if b"DD2 " not in sec: continue
    o,s = sec[b"DIM "]; b=g.bytes_at(o,s); W=b[0]|(b[1]<<8); H=b[2]|(b[3]<<8)
    o2,s2 = sec[b"ERA "]; b2=g.bytes_at(o2,s2); ts=b2[0]|(b2[1]<<8)
    off, sz = sec[b"DD2 "]
    mx = 0; mn = 99999
    for i in range(0, sz-7, 8):
        t = g.u16(off+i)
        mx = max(mx,t); mn=min(mn,t)
    rows.append((TILESET.get(ts) or ("ts%d"%ts), os.path.basename(p), W, H, sz, sz%8, mn, mx, len(gaps)))

print(f"{'tileset':10s} {'map':34s} {'dim':10s} {'size':>6s} {'%8':>3s} {'min':>6s} {'max':>7s} {'gaps'}")
for r in sorted(rows, key=lambda z: (str(z[0]), z[1])):
    flag = "  <<<" if r[7] > 500 else ""
    print(f"{r[0]:10s} {r[1][:34]:34s} {r[2]}x{r[3]:<6d} {r[4]:6d} {r[5]:3d} {r[6]:6d} {r[7]:7d} {r[8]}{flag}")



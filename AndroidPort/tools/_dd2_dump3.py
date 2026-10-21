import os, sys, glob
sys.path.insert(0, ".")
import pipeline_maps as pm

TARGETS = ["Lost Civilization","Lost Temple","Green Valleys","Crystal Castles","Blood Bath","The Small Divide","Inferno","Sanctuary"]
cands = sorted(glob.glob(r"F:\KF\XJZB\maps\**\*.sc*", recursive=True))
for p in cands:
    base = os.path.splitext(os.path.basename(p))[0]
    if not any(t in base for t in TARGETS): continue
    r = pm.read_chk(p)
    if not r: continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    if b"DD2 " not in sec: continue
    o,s = sec[b"DIM "]; b=g.bytes_at(o,s); W=b[0]|(b[1]<<8); H=b[2]|(b[3]<<8)
    o2,s2 = sec[b"ERA "]; b2=g.bytes_at(o2,s2); ts=b2[0]|(b2[1]<<8)
    off, sz = sec[b"DD2 "]
    n = sz//8
    print(f"=== {base}  ts={ts} {W}x{H} ({W*32}x{H*32}px) size={sz} n={n}")
    bad = 0
    for i in range(n):
        t = g.u16(off+i*8); x = g.u16(off+i*8+2); y = g.u16(off+i*8+4)
        ok = (x < W*32 and y < H*32)
        if not ok: bad += 1
        if i < 12 or not ok:
            print(f"   [{i:3d}] t={t:6d} x={x:5d} y={y:5d} {'OK' if ok else 'BAD'}")
    print(f"   -> bad xy = {bad}/{n}")

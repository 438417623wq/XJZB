import os, sys, glob
sys.path.insert(0, ".")
import pipeline_maps as pm
cands = sorted(set(glob.glob(r"F:\KF\XJZB\maps\**\*.sc*", recursive=True)))
tgt = [p for p in cands if "Inferno" in p]
print(tgt)
p = tgt[0]
chk, gaps = pm.read_chk(p)
g, sec = pm.parse_chk(chk, gaps)
print("gaps:", gaps)
print("sections:", [(k.decode("latin1"), v[1]) for k,v in sec.items()])
off, sz = sec[b"DD2 "]
raw = g.bytes_at(off, sz)
print("off", off, "size", sz, "len raw", len(raw))
for i in range(0, min(sz, 160), 8):
    b = raw[i:i+8]
    u16 = [b[j] | (b[j+1]<<8) for j in (0,2,4,6)]
    print(f"  rec{i//8:3d} {' '.join('%02x'%c for c in b)}  u16={u16}")

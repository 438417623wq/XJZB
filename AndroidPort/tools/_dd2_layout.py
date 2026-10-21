import os, sys, glob, collections
sys.path.insert(0, ".")
import pipeline_maps as pm

TILESET = {0:"badlands",1:"platform",2:"install",3:"ashworld",4:"jungle"}

def sec_of(p):
    r = pm.read_chk(p)
    if not r: return None
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    if b"DD2 " not in sec or b"DIM " not in sec or b"ERA " not in sec: return None
    o,s = sec[b"DIM "]; b=g.bytes_at(o,s); W=b[0]|(b[1]<<8); H=b[2]|(b[3]<<8)
    o,s = sec[b"ERA "]; b=g.bytes_at(o,s); ts=b[0]|(b[1]<<8)
    o,s = sec[b"DD2 "]
    return (g, o, s, W, H, ts, gaps)

# section size divisibility survey
print("=== DD2 size divisibility ===")
div = collections.Counter()
sizes = []
cands = sorted(glob.glob(r"F:\KF\XJZB\maps\**\*.sc*", recursive=True))
info = []
for p in cands:
    x = sec_of(p)
    if not x: continue
    g,o,s,W,H,ts,gaps = x
    sizes.append(s)
    info.append((os.path.basename(p), s, W, H, ts, gaps))
    div[s % 8] += 1
print("size%8 histogram:", dict(div), " n=", len(sizes))
print("sample:", info[:6])
print()

print("=== layout brute force: (size, header) vs valid-coord fraction ===")
best = {}
for (name, s, W, H, ts, gaps) in info:
    pass
for recsz in (6,8,9,10,12,16):
    for hdr in (0,1,2,4,8):
        ok = tot = 0
        for (name, s, W, H, ts, gaps) in info:
            x = sec_of(os.path.join(r"F:\KF\XJZB\maps", name)) if False else None
        # faster: precompute per map below
print("(skip)")

# do it properly with cached data
cache = []
for (name, s, W, H, ts, gaps) in info:
    # re-find path
    cache.append((name, s, W, H, ts, gaps))

def score(recsz, hdr):
    ok = tot = 0
    for p in cands:
        x = sec_of(p)
        if not x: continue
        g,o,s,W,H,ts,gaps = x
        n = (s - hdr) // recsz
        for i in range(n):
            base = o + hdr + i*recsz
            if any(base < gp+gs and base+recsz-1 >= gp for gp,gs in gaps): continue
            b = g.bytes_at(base, recsz)
            t = b[0]|(b[1]<<8); xx = b[2]|(b[3]<<8); yy = b[4]|(b[5]<<8)
            tot += 1
            if xx < W and yy < H: ok += 1
    return ok, tot

for recsz in (6,8,9,10,12,16):
    for hdr in (0,1,2,4,8):
        ok, tot = score(recsz, hdr)
        if tot:
            print(f"recsz={recsz:3d} hdr={hdr} valid={ok}/{tot} = {ok/tot:.4f}")

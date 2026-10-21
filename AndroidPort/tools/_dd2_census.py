import os, sys, glob, collections
sys.path.insert(0, ".")
import pipeline_maps as pm

TILESET = {0:"badlands",1:"platform",2:"install",3:"ashworld",4:"jungle"}
cands = sorted(set(glob.glob(r"F:\KF\XJZB\maps\**\*.sc*", recursive=True) + glob.glob(r"F:\KF\XJZB\*.sc*")))
print("maps:", len(cands))
by_ts = collections.defaultdict(collections.Counter)
sizes = collections.Counter()
allids = collections.Counter()
info = {}
for p in cands:
    r = pm.read_chk(p)
    if not r: continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    ts = None
    if b"ERA " in sec:
        off, sz = sec[b"ERA "]
        b = g.bytes_at(off, sz)
        ts = b[0] | (b[1]<<8)
    w = h = None
    if b"DIM " in sec:
        off, sz = sec[b"DIM "]
        b = g.bytes_at(off, sz)
        w = b[0]|(b[1]<<8); h = b[2]|(b[3]<<8)
    name = os.path.splitext(os.path.basename(p))[0]
    if b"DD2 " not in sec:
        info[name] = (ts, w, h, 0, [], -1)
        continue
    off, sz = sec[b"DD2 "]
    raw = g.bytes_at(off, sz)
    sizes[sz % 8] += 1
    ids = []
    for i in range(0, sz - 7, 8):
        b = raw[i:i+8]
        ids.append(b[0] | (b[1]<<8))
    tname = TILESET.get(ts, str(ts))
    by_ts[tname].update(ids)
    allids.update(ids)
    info[name] = (ts, w, h, sz, ids, len(ids))

print("size%8 distribution:", dict(sizes))
print()
print(f"{'map':22s} {'tileset':9s} {'w x h':9s} {'bytes':>6s} {'n':>4s}  ids")
for name,(ts,w,h,sz,ids,n) in sorted(info.items()):
    tname = TILESET.get(ts, str(ts))
    show = ",".join(str(x) for x in ids[:14])
    if len(ids) > 14: show += ",..."
    print(f"{name:22s} {tname:9s} {str(w)+'x'+str(h):9s} {sz:6d} {n:4d}  {show}")
print()
print("=== distinct ids per tileset ===")
for tname in ("badlands","platform","install","ashworld","jungle"):
    c = by_ts[tname]
    if not c: continue
    ks = sorted(c)
    print(f"{tname}: {len(ks)} distinct, min={ks[0]} max={ks[-1]}")
    print("   ", ks)
print()
print("ALL distinct ids:", len(allids), "min", min(allids), "max", max(allids))

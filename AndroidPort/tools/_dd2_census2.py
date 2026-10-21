import os, sys, glob, collections
sys.path.insert(0, ".")
import pipeline_maps as pm

TILESET = {0:"badlands",1:"platform",2:"install",3:"ashworld",4:"jungle"}
cands = sorted(set(glob.glob(r"F:\KF\XJZB\maps\**\*.sc*", recursive=True)))
by_ts = collections.defaultdict(collections.Counter)
gap_hits = 0
for p in cands:
    r = pm.read_chk(p)
    if not r: continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    if b"ERA " not in sec or b"DD2 " not in sec: continue
    o, s = sec[b"ERA "]; b = g.bytes_at(o, s); ts = b[0] | (b[1]<<8)
    off, sz = sec[b"DD2 "]
    tname = TILESET.get(ts, "ts%d" % ts)
    for i in range(0, sz - 7, 8):
        base = off + i
        # skip records overlapping a gap
        bad = any(base < gp + gs and base + 7 >= gp for gp, gs in gaps)
        if bad:
            gap_hits += 1
            continue
        raw = g.bytes_at(base, 8)
        by_ts[tname][raw[0] | (raw[1]<<8)] += 1
print("gap-affected records skipped:", gap_hits)
print()
for tname in ("badlands","platform","install","ashworld","jungle"):
    c = by_ts[tname]
    ks = sorted(c)
    print(f"=== {tname}: {len(ks)} distinct ids, min={ks[0]} max={ks[-1]}, records={sum(c.values())}")
    print("   ", ks)
    print()

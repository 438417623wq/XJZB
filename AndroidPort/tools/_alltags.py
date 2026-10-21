import os, sys, glob, collections
sys.path.insert(0, ".")
import pipeline_maps as pm

tags = collections.Counter()
sizes = collections.defaultdict(list)
cands = sorted(glob.glob(r"F:\KF\XJZB\maps\**\*.sc*", recursive=True))
n = 0
for p in cands:
    r = pm.read_chk(p)
    if not r: continue
    n += 1
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    for t,(o,s) in sec.items():
        tags[t] += 1
        sizes[t].append(s)
print("maps:", n)
for t,c in sorted(tags.items(), key=lambda z:-z[1]):
    nm = t.decode('latin1')
    ss = sizes[t]
    print(f"{nm!r:12s} count={c:4d} minsz={min(ss):7d} maxsz={max(ss):7d}")

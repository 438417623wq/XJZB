import os, sys, collections
sys.path.insert(0, ".")
import pipeline_maps as pm
# census DDDATA and DD2 across ALL maps we can find on disk
import glob
cands = []
for root in (r"F:\KF\XJZB\maps", r"F:\KF\XJZB"):
    for ext in ("*.scm", "*.scx"):
        cands += glob.glob(os.path.join(root, "**", ext), recursive=True)
cands = sorted(set(cands))
print("candidate maps on disk:", len(cands))
tags = collections.Counter()
for p in cands:
    try:
        r = pm.read_chk(p)
    except Exception as e:
        continue
    if not r: continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    has_dd = b"DDDATA" in sec
    has_dd2 = b"DD2 " in sec
    tags[(has_dd, has_dd2)] += 1
    if has_dd:
        print("  DDDATA", os.path.basename(p), sec[b"DDDATA"][1])
print("(DDDATA, DD2) counts:", dict(tags))

import os, sys
from collections import Counter
sys.path.insert(0, '.')
import pipeline_maps as pm
for ts in ['jungle','platform','ice','twilight','desert','badlands','install','ashworld']:
    t=pm.load_tileset(ts)
    cnt=Counter()
    for flags in t['vf4_flags']:
        for f in flags: cnt[f]+=1
    tot=sum(cnt.values())
    bit0=sum(v for f,v in cnt.items() if f&1)
    anyf=sum(v for f,v in cnt.items() if f!=0)
    top=cnt.most_common(6)
    print("%-9s tot=%6d bit0=%5.0f%% any=%5.0f%% top=%s" % (
        ts, tot, 100.0*bit0/tot, 100.0*anyf/tot, top))

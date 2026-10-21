"""v2.42 closeout step 1: full re-bake of every shipped map with the v2 void rule.

Idempotent and overwriting: it regenerates every map's chunk PNGs from the
source archives, so the mixed (half-rebaked) asset tree is replaced wholesale.
Run slim_assets.py --yes afterwards to fold the PNGs back into webp.
"""
import os, sys, json, time
sys.path.insert(0, r'F:\KF\XJZB\AndroidPort\tools')
import pipeline_maps as pm

SHIPPED = {mid: src for src, mid, _n, _g in pm.MAPS}
for mid, src in [("bloodbath", r"maps\(4)Blood Bath.scm"),
                 ("bottleneck", r"maps\(2)Bottleneck.scm"),
                 ("boxer", r"maps\(2)Boxer.scm"),
                 ("hunters", r"maps\(8)The Hunters.scm"),
                 ("darkcrystal", r"maps\(4)Dark Crystal.scm"),
                 ("river", r"maps\(2)River Crossing.scm"),
                 ("3kingdoms", r"maps\(3)Three Kingdoms.scm"),
                 ("divide", r"maps\(2)The Small Divide.scm"),
                 ("cyclone", r"maps\(4)Cyclone.scm"),
                 ("volcanis", r"maps\(2)Volcanis.scm")]:
    SHIPPED.setdefault(mid, src)

print('shipped maps: %d' % len(SHIPPED), flush=True)
ok = fail = 0
t0 = time.time()
for i, mid in enumerate(sorted(SHIPPED), 1):
    src = SHIPPED[mid]
    mdir = os.path.join(pm.OUT, 'maps', mid)
    try:
        name = json.load(open(os.path.join(mdir, 'meta.json'), encoding='utf8')).get('name', mid)
    except Exception:
        name = mid
    t = time.time()
    try:
        good = pm.build_map(src, mid, name)
    except Exception as e:
        print('EXC %-16s %s: %s' % (mid, type(e).__name__, e), flush=True)
        good = False
    if good:
        ok += 1
    else:
        fail += 1
    print('[%2d/%d] %-16s %-4s %5.1fs elapsed=%5.1fs'
          % (i, len(SHIPPED), mid, 'ok' if good else 'FAIL',
             time.time() - t, time.time() - t0), flush=True)
pm.write_map_index()
print('re-baked %d/%d fail=%d total=%.1fs' % (ok, len(SHIPPED), fail, time.time() - t0))
print('index.txt rewritten')

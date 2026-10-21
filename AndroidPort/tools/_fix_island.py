"""v2.42 closeout: repair the island flag on the shipped asset tree.

build_map fed raw CHK pixel start coordinates into connectivity(), whose walk
bitmap is a minitile grid (w*4). Every start snapped to nothing and every map
was recorded as an island (island=1). map_census/add_elevation used the
minitile _starts_of and were always correct, so only build_map's output -- the
meta.json / meta.txt written by the 52-map re-bake -- needs rewriting.

This rewrites the two flags in place (no terrain re-render, no webp touch) and
regenerates maps/index.txt from the corrected meta.json files.
"""
import os, sys, json
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


def rewrite_txt(path, connected):
    """Drop elev=/island= and re-insert them right after tileset=, the order
    build_map and add_elevation both produce."""
    with open(path, 'r', encoding='utf8') as fp:
        lines = [ln.rstrip('\n') for ln in fp.readlines()]
    out, seen = [], False
    for ln in lines:
        if ln.startswith('elev=') or ln.startswith('island='):
            continue
        out.append(ln)
        if ln.startswith('tileset=') and not seen:
            out.append('elev=1')
            if not connected:
                out.append('island=1')
            seen = True
    if not seen:
        out.append('elev=1')
        if not connected:
            out.append('island=1')
    with open(path, 'w', encoding='utf8') as fp:
        fp.write('\n'.join(out))


fixed = 0
for mid in sorted(SHIPPED):
    mdir = os.path.join(pm.OUT, 'maps', mid)
    mjson = os.path.join(mdir, 'meta.json')
    if not os.path.exists(mjson):
        print('SKIP %-16s no meta.json' % mid, flush=True)
        continue
    # recompute with the same chain build_map now uses
    r = pm.read_chk(os.path.join(pm.ROOT, SHIPPED[mid]))
    if not r:
        print('SKIP %-16s unreadable source' % mid, flush=True)
        continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    off, _ = sec[b'DIM ']
    w, h = g.u16(off), g.u16(off + 2)
    eoff, _ = sec[b'ERA ']
    ts = pm.load_tileset(pm.TILESETS.get(g.byte(eoff), 'platform'))
    moff, _ = sec[b'MTXM']
    mtwm = [g.u16(moff + i * 2) for i in range(w * h)]
    walk = pm._walk_bitmap(w, h, mtwm, ts)
    starts = pm._starts_of(g, sec)
    connected, _ = pm.connectivity(walk, starts)

    meta = json.load(open(mjson, encoding='utf8'))
    was = meta.get('island')
    now = 0 if connected else 1
    if was != now:
        fixed += 1
    meta['island'] = now
    with open(mjson, 'w', encoding='utf8') as fp:
        json.dump(meta, fp, ensure_ascii=False)
    rewrite_txt(os.path.join(mdir, 'meta.txt'), connected)
    print('%-16s island %s -> %s %s' % (
        mid, was, now, 'ISLAND' if not connected else ''), flush=True)

pm.write_map_index()
print('repaired %d meta.json, index.txt rewritten' % fixed)

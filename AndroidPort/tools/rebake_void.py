"""v2.42 batch A: re-bake every shipped map whose CHK carries void tiles."""
import os, sys, json
sys.path.insert(0, r'F:\KF\XJZB\AndroidPort\tools')
import pipeline_maps as pm

SHIPPED = {}
for src, mid, name, group in pm.MAPS:
    SHIPPED[mid] = src
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

VOID = ['bottleneck', 'boxer', 'divide', '3kingdoms', 'cyclone', 'darkcrystal',
        'islandhop', 'newgettysburg', 'junglerumble', 'killingfields',
        'plainsofsnow', 'riverruns', 'hunters', 'steppingstones', 'archipelago',
        'kakarukeys', 'nightfall', 'riverlethe', 'sanctuary', 'closeencounters',
        'hypothermia', 'sirocco', 'thinice', 'brokensteppes', 'frozensea',
        'primevalisles', 'theatreofwar', 'tribes', 'tripleteam', 'doublediamond',
        'crossroads', 'biggamehunters', 'ashrigo', 'losttemple', 'provinggrounds',
        'rivalry', 'acropolis', 'bonecanyon', 'crusader', 'remoteoutpost']

ok = 0
for mid in VOID:
    src = SHIPPED.get(mid)
    if src is None:
        print('NO SOURCE for', mid); continue
    mdir = os.path.join(pm.OUT, 'maps', mid)
    name = mid
    try:
        meta = json.load(open(os.path.join(mdir, 'meta.json'), encoding='utf8'))
        name = meta.get('name', mid)
    except Exception:
        pass
    if pm.build_map(src, mid, name):
        ok += 1
print('re-baked %d/%d' % (ok, len(VOID)))
pm.write_map_index()
print('index.txt rewritten')

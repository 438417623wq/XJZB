"""Parse the CHK DD2 (doodad placement) section of the bundled maps.

These .scm files use the post-1.18 tag `DD2 ` rather than the classic
`DDDATA`.  Both carry the same 8-byte record:

    u16 doodadType   index into the doodad table (== the ddNNN.png number)
    u16 x            pixel position on the 32 px/tile grid
    u16 y
    u8  owner        player who "owns" it (0 = neutral)
    u8  percent      validity byte, normally 100

This probe prints the per-map doodad census and cross-checks every id
against the extracted ddNNN.png art, which decides whether batch D's
doodad layer can ship.
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pipeline_maps as pm

MAPS = [
    ("maps\\(4)Blood Bath.scm", "bloodbath"),
    ("maps\\(2)Bottleneck.scm", "bottleneck"),
    ("maps\\(2)Boxer.scm", "boxer"),
    ("maps\\(8)The Hunters.scm", "hunters"),
    ("maps\\(4)Dark Crystal.scm", "darkcrystal"),
    ("maps\\(3)Three Kingdoms.scm", "3kingdoms"),
    ("maps\\(2)The Small Divide.scm", "divide"),
    ("maps\\(4)Cyclone.scm", "cyclone"),
    ("maps\\(2)Volcanis.scm", "volcanis"),
    ("maps\\(2)River Crossing.scm", "river"),
]

DOODAD_DIR = r"F:\KF\XJZB\AndroidPort\extracted\expand\doodads"
all_ids = collections.Counter()
missing_all = set()

for src, mid in MAPS:
    r = pm.read_chk(os.path.join(pm.ROOT, src))
    if not r:
        print(f"{mid:12s} UNREADABLE")
        continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    if b"DD2 " not in sec:
        print(f"{mid:12s} no DD2")
        continue
    off, size = sec[b"DD2 "]
    n = size // 8
    ids = collections.Counter()
    sample = []
    pcts = collections.Counter()
    for i in range(n):
        b = off + i * 8
        did = g.u16(b)
        x = g.u16(b + 2)
        y = g.u16(b + 4)
        own = g.byte(b + 6)
        pct = g.byte(b + 7)
        ids[did] += 1
        pcts[pct] += 1
        if len(sample) < 5:
            sample.append((did, x, y, own, pct))
    all_ids.update(ids)
    print(f"{mid:12s} size={size} entries={n} distinct={len(ids)} pct={dict(pcts)}")
    print(f"             top: {ids.most_common(10)}")
    print(f"             sample: {sample}")
    miss = sorted(i for i in ids
                  if not os.path.exists(os.path.join(DOODAD_DIR, f"dd{i:03d}.png")))
    if miss:
        missing_all.update(miss)
        print(f"             MISSING art: {miss}")

print(f"\nALL distinct doodad ids used: {len(all_ids)}")
print(f"ids: {sorted(all_ids)}")
print(f"missing art overall: {sorted(missing_all)}")

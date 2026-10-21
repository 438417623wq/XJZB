"""Census the CHK sections present in the bundled maps.

Batch D expects a DDDATA (doodad placement) section, but none of the
bundled .scm files appear to carry one.  This probe lists every section
tag and size so we can tell whether the doodad data is simply absent from
these maps (in which case batch D has nothing to render) or is hiding
under a different tag / an unparsed offset.
"""
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

for src, mid in MAPS:
    r = pm.read_chk(os.path.join(pm.ROOT, src))
    if not r:
        print(f"{mid:12s} UNREADABLE")
        continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    tags = sorted(sec.keys())
    print(f"{mid:12s} {len(sec)} sections, chk={len(chk)}B gaps={sum(s for _, s in gaps)}")
    print("             " + " ".join(
        f"{t.decode('latin1').strip()}({sec[t][1]})" for t in tags))

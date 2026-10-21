import re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
t = open(r"F:\KF\XJZB\AndroidPort\tools\pipeline_expand.py", encoding="utf-8", errors="replace").read()
i = t.find("DOODAD_FIXUPS")
j = t.find("]", i)
print(t[i:j+1])
print("=== images_tbl.txt thingy entries ===")
import os
for fn in ("images_tbl.txt","images_tbl2.txt"):
    p = os.path.join(r"F:\KF\XJZB\AndroidPort\tools", fn)
    if not os.path.exists(p): print(fn, "MISSING"); continue
    lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
    thingy = [(k, l) for k, l in enumerate(lines) if "thingy" in l.lower()]
    print(fn, "total", len(lines), "thingy", len(thingy))
    for k, l in thingy[:12]: print("   ", k, l)

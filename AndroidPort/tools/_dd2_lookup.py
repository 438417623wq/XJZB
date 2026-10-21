import re, collections
txt = open("_bwenums.h", encoding="utf8", errors="replace").read()
m = re.search(r"enum\s+struct\s+SpriteTypes\s*:\s*int\s*\{(.*?)\};", txt, re.S)
out=[]; cur=0
for part in m.group(1).split(","):
    part=part.strip()
    if not part: continue
    mm = re.match(r"([A-Za-z_0-9]+)\s*(?:=\s*(-?\d+))?", part)
    if not mm: continue
    v = int(mm.group(2)) if mm.group(2) else cur
    cur = v+1
    out.append((v, mm.group(1)))
d = dict(out)
print("=== SpriteTypes lookup for DD2 ids seen ===")
for k in [0,1,2,3,35,61,65,137,158,159,196,197,256,257,258,259,268,269,270,271,272,273,276,287,294,299,300,311,325,329,330]:
    print(f"  {k:4d} -> {d.get(k,'<none>')}")

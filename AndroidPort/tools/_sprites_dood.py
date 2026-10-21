import re
txt = open("_bwenums.h", encoding="utf8", errors="replace").read()
m = re.search(r"enum\s+struct\s+SpriteTypes\s*:\s*int\s*\{(.*?)\};", txt, re.S)
body = m.group(1)
out=[]; cur=0
for part in body.split(","):
    part = part.strip()
    if not part: continue
    mm = re.match(r"([A-Za-z_0-9]+)\s*(?:=\s*(-?\d+))?", part)
    if not mm: continue
    v = int(mm.group(2)) if mm.group(2) else cur
    cur = v+1
    out.append((v, mm.group(1)))
dood = [x for x in out if x[0] <= 129]
print("doodad-range entries:", len(dood))
for v,n in dood:
    print(f"  {v:4d} {n}")

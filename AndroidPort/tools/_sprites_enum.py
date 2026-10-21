import re
txt = open("_bwenums.h", encoding="utf8", errors="replace").read()
def enum(name):
    m = re.search(r"enum\s+struct\s+" + name + r"\s*:\s*int\s*\{(.*?)\n\};", txt, re.S)
    if not m:
        m = re.search(r"enum\s+struct\s+" + name + r"\s*:\s*int\s*\{(.*?)\};", txt, re.S)
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
    return out
for nm in ("SpriteTypes",):
    vals = enum(nm)
    print(f"=== {nm}: {len(vals)} entries, max={vals[-1][0]} ===")
    for v,n in vals[:20]: print(f"  {v:4d} {n}")
    print("  ...")
    tail = [x for x in vals if x[0] >= 130]
    print("  entries with value >= 130:", len(tail))
    for v,n in tail[:60]: print(f"  {v:4d} {n}")

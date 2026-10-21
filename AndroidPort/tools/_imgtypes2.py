import re
txt = open("_bwenums.h", encoding="utf8", errors="replace").read()
def enum(name):
    m = re.search(r"enum\s+struct\s+"+name+r"\s*:\s*int\s*\{(.*?)\};", txt, re.S)
    out=[]; cur=0
    for part in m.group(1).split(","):
        part=part.strip()
        if not part: continue
        mm = re.match(r"([A-Za-z_0-9]+)\s*(?:=\s*(-?\d+))?", part)
        if not mm: continue
        v = int(mm.group(2)) if mm.group(2) else cur
        cur = v+1
        out.append((v, mm.group(1)))
    return out
it = enum("ImageTypes")
print("ImageTypes count", len(it), "max", max(v for v,_ in it))
for v,n in it:
    if v >= 555 and v <= 730:
        print(v, n)
print("--- all names containing IMAGEID ---")
for v,n in it:
    if "IMAGEID" in n: print(v, n)

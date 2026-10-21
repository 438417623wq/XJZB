import re
txt = open("_bwenums.h", encoding="utf8", errors="replace").read()
def enum(name):
    m = re.search(r"enum\s+struct\s+" + name + r"\s*:\s*int\s*\{(.*?)\};", txt, re.S)
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
d = dict(it)
print("ImageTypes count", len(it), "max", it[-1][0])
for k in [128,129,130,131,137,196,197,200,210,240,250,251,252,253,254,255,256,257,258,259,260,287,557,558,600,686,718]:
    print(f"  ImageTypes {k:4d} -> {d.get(k,'<none>')}")

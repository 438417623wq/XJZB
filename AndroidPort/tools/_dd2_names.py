import os, sys, glob, re, collections
sys.path.insert(0, ".")
import pipeline_maps as pm

txt = open("_bwenums.h", encoding="utf8", errors="replace").read()
m = re.search(r"enum\s+struct\s+SpriteTypes\s*:\s*int\s*\{(.*?)\};", txt, re.S)
sp=[]; cur=0
for part in m.group(1).split(","):
    part=part.strip()
    if not part: continue
    mm = re.match(r"([A-Za-z_0-9]+)\s*(?:=\s*(-?\d+))?", part)
    if not mm: continue
    v = int(mm.group(2)) if mm.group(2) else cur
    cur = v+1
    sp.append((v, mm.group(1)))
SP = dict(sp)

TILESET = {0:"badlands",1:"platform",2:"install",3:"ashworld",4:"jungle"}
cands = sorted(set(glob.glob(r"F:\KF\XJZB\maps\**\*.sc*", recursive=True) + glob.glob(r"F:\KF\XJZB\*.sc*")))
allids = collections.Counter()
permap = {}
for p in cands:
    r = pm.read_chk(p)
    if not r: continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    if b"DD2 " not in sec: continue
    off, sz = sec[b"DD2 "]
    raw = g.bytes_at(off, sz)
    ids = [raw[i] | (raw[i+1]<<8) for i in range(0, sz-7, 8)]
    allids.update(ids)
    permap[os.path.splitext(os.path.basename(p))[0]] = ids

print("distinct ids:", len(allids), "min", min(allids), "max", max(allids))
print()
print("id   count  SpriteTypes name")
for k in sorted(allids):
    print(f"{k:5d} {allids[k]:5d}  {SP.get(k,'<out of range>')}")

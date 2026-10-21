import sys, os, struct, re, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = r"F:\KF\XJZB\scr_research\tileset"
T = r"F:\KF\XJZB\AndroidPort\tools"
print("### 1. all-zero 52B records per cv5 (padding hypothesis)")
for ts in ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]:
    b = open(os.path.join(D, ts + ".cv5"),"rb").read()
    n = len(b)//52
    z = sum(1 for g in range(n) if b[g*52:(g+1)*52] == bytes(52))
    # trailing zero length
    tz = len(b) - len(b.rstrip(b"\x00"))
    print(f"  {ts:9s} groups={n:5d} all-zero={z:5d} ({100*z/n:.0f}%) trailing_zero_bytes={tz} csize_hint")
print()
print("### 2. mid-file records")
for ts in ["badlands","platform"]:
    b = open(os.path.join(D, ts + ".cv5"),"rb").read()
    n = len(b)//52
    print(" ", ts)
    for g in (n//4, n//2, 3*n//4, n-1):
        print(f"   g{g}: {b[g*52:g*52+26].hex(' ')}")
print()
print("### 3. ddNNN gap hypothesis (jungle)")
sys.path.insert(0, T)
import sc_archive
a = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
data, gaps = a.read_with_gaps("tileset\\jungle\\dddata.bin")
print("  jungle dddata gaps:", gaps)
def ent(pos): return pos//512
miss = [56, 203, 204, 205, 206, 207, 209]
for m in miss:
    hit = [g for g in gaps if ent(g[0]) <= m <= ent(g[0]+g[1]-1)]
    print(f"   id {m}: in gap? {bool(hit)} {hit}")
print()
print("### 4. tileset dirs in images_tbl2 / listfile")
lines = open(os.path.join(T,"images_tbl2.txt"), encoding="utf-8", errors="replace").read().splitlines()
tsdirs = collections.Counter()
for l in lines:
    low = l.lower()
    for t in ("desert","ice","twilight"):
        if f"tileset\\{t}\\" in low: tsdirs[t]+=1
print("  images_tbl2 doodad-overlay-style entries per bw tileset:", dict(tsdirs))
lf = os.path.join(T,"listfile_BrooDat.txt")
if os.path.exists(lf):
    names = open(lf, encoding="utf-8", errors="replace").read().splitlines()
    for t in ("desert","ice","twilight"):
        hits = [x for x in names if f"tileset\\{t}\\" in x.lower() and x.lower().endswith(".grp")]
        print(f"  listfile BrooDat tileset\\{t}\\*.grp count={len(hits)} sample={hits[:6]}")

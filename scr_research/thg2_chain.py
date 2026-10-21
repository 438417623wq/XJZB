import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm, sc_archive
T = r"F:\KF\XJZB\AndroidPort\tools"
img = {}
for line in open(os.path.join(T, "images_tbl2.txt"), encoding="latin1"):
    if "\t" in line:
        a, b = line.rstrip("\n").split("\t", 1)
        if a.strip().isdigit(): img[int(a)] = b.strip()
sd = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
sp, _ = sd.read_with_gaps("arr\\sprites.dat")
def spr(i): return struct.unpack_from("<HBBHH", sp, i*8)
for p in [r"F:\KF\XJZB\maps\(4)Blood Bath.scm",
          r"F:\KF\XJZB\maps\BroodWar\WebMaps\(4)Inferno.scm"]:
    chk, gaps = pm.read_chk(p); g, sec = pm.parse_chk(chk, gaps)
    o, s = sec[b"THG2"]; raw = g.bytes_at(o, s)
    recs = [struct.unpack_from("<HHHBBH", raw, i) for i in range(0, s, 10)]
    print("#"*12, os.path.basename(p), "THG2 recs", len(recs))
    seen = {}
    for (sid, x, y, own, un, fl) in recs:
        seen.setdefault(sid, []).append(fl)
    for sid in sorted(seen):
        im, dx, dy, hp, sf = spr(sid)
        print(f"  spriteId={sid:3d} n={len(seen[sid])} flags={sorted(set(seen[sid]))} -> sprites.dat image={im} {img.get(im,'?')}")

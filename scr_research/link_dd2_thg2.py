import sys, os, glob, struct, collections
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
def spr_img(i):
    if i*8+8 > len(sp): return None
    return struct.unpack_from("<H", sp, i*8)[0]

def load(p):
    chk, gaps = pm.read_chk(p); g, sec = pm.parse_chk(chk, gaps)
    o, s = sec[b"ERA "]; era = g.bytes_at(o, s)[0]
    o, s = sec[b"DD2 "]; dd = [struct.unpack_from("<HHHBB", g.bytes_at(o, s), i) for i in range(0, s, 8)]
    tg = []
    if b"THG2" in sec:
        o, s = sec[b"THG2"]
        tg = [struct.unpack_from("<HHHBBH", g.bytes_at(o, s), i) for i in range(0, s, 10)]
    return era, dd, tg

cands = sorted(glob.glob(r"F:\KF\XJZB\AndroidPort\assets_src\maps\*.chk")) + \
        sorted(glob.glob(r"F:\KF\XJZB\maps\**\*.sc*", recursive=True))
link = collections.defaultdict(collections.Counter)
near = []
nmap = 0
for p in cands:
    try:
        era, dd, tg = load(p)
    except Exception:
        continue
    if not dd or not tg: continue
    nmap += 1
    tpos = {(x, y): sid for (sid, x, y, own, un, fl) in tg}
    for (eid, xc, yc, own, dis) in dd:
        for (tx, ty), sid in tpos.items():
            if abs(tx-xc) <= 16 and abs(ty-yc) <= 16:
                im = spr_img(sid)
                link[eid][(sid, img.get(im, "?"))] += 1
print("maps with both DD2 and THG2:", nmap)
for eid in sorted(link):
    tot = sum(link[eid].values())
    top = link[eid].most_common(3)
    print(f"  ddData id {eid:4d}: n={tot:4d}  " + " | ".join(f"sprite{sid}->{nm}" for (sid, nm), c in top))

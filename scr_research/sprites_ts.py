import sys, os, struct, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
T = r"F:\KF\XJZB\AndroidPort\tools"
img = {}
for l in open(os.path.join(T,"images_tbl2.txt"), encoding="utf-8", errors="replace"):
    a,b = l.rstrip("\n").split("\t",1); img[int(a)] = b
sys.path.insert(0, T)
import sc_archive
a = sc_archive.Archive(r"F:\KF\XJZB\BrooDat.mpq")
data, gaps = a.read_with_gaps("arr\\sprites.dat")
n = len(data)//8
print("sprite records:", n)
# sprites whose image is a tileset doodad overlay
rows = []
for r in range(n):
    im = struct.unpack_from("<H", data, r*8)[0]
    name = img.get(im, "")
    if "thingy\\tileset\\" in name.lower():
        rows.append((r, im, name))
print("tileset-overlay sprites:", len(rows))
per = {}
for r, im, name in rows:
    ts = name.lower().split("tileset\\")[1].split("\\")[0]
    per.setdefault(ts, []).append((r, im, os.path.basename(name)))
for ts, v in per.items():
    print(f"  {ts}: {len(v)} sprites  ids {v[0][0]}..{v[-1][0]}")
    print("      ", [(x[0], x[2]) for x in v][:12])

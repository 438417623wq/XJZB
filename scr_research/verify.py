import sys, os, struct, pickle, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive
from gapio import GapReader
summary = pickle.load(open(r"F:\KF\XJZB\scr_research\cv5_doodads.pkl","rb"))
print("=== verify: #groups per id == height, and sum(heights) == #doodad groups ===")
for ts in ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]:
    ng, ids, rem1, d = summary[ts]
    ok = 0; bad = []
    tot_h = 0
    for eid, recs in d.items():
        h = recs[0][6]; tot_h += h
        if len(recs) == h: ok += 1
        else: bad.append((eid, len(recs), h))
    print(f"  {ts:9s} ids={len(d):4d} matching(height==groupcount)={ok:4d} sum(heights)={tot_h:4d} actualGroups={sum(len(v) for v in d.values()):4d} mismatches={bad[:5]}")

print()
print("=== does ddNNN.grp name == doodad id? (jungle named GRPs) ===")
img = {}
for line in open(r"F:\KF\XJZB\AndroidPort\tools\images_tbl2.txt", encoding="latin1"):
    if "\t" in line:
        a, b = line.rstrip("\n").split("\t", 1)
        if a.strip().isdigit(): img[int(a)] = b.strip()
sd = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
sp, _ = sd.read_with_gaps("arr\\sprites.dat")
def spr(i):
    if i*8+8 > len(sp): return None
    return struct.unpack_from("<H", sp, i*8)[0]
for ts, cand in [("jungle", [25,26,27,28,29,30,31,55,56,75,76,77,78,79,80,81,91,203,204,205,206,207,209,210,211]),
                 ("platform",[137,256,257,258]),
                 ("ashworld",[0,1,45,46,122,142])]:
    _, _, _, d = summary[ts]
    print(f"  -- {ts}")
    for eid in cand:
        if eid not in d: print(f"     id {eid:4d}: ABSENT"); continue
        k, flags, ov, rem, nm, w, h = d[eid][0]
        grp = ""
        if flags & 0x1000:
            im = spr(ov); grp = (img.get(im,"?") if im is not None else "?")
        print(f"     id {eid:4d}: w={w:2d} h={h:2d} flags=0x{flags:04x} {'SPR' if flags&0x1000 else ('UNIT' if flags&0x2000 else 'terrain')} GRP={grp}")

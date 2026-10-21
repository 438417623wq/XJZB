import sys, os, struct, collections, pickle
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import sc_archive
from gapio import GapReader
summary = pickle.load(open(r"F:\KF\XJZB\scr_research\cv5_doodads.pkl","rb"))

# stat_txt.tbl
st = open(r"F:\KF\XJZB\AndroidPort\tools\stat_txt.txt", encoding="latin1").read().splitlines()
# images.tbl index -> path
img = {}
for line in open(r"F:\KF\XJZB\AndroidPort\tools\images_tbl2.txt", encoding="latin1"):
    if "\t" in line:
        a, b = line.rstrip("\n").split("\t", 1)
        if a.strip().isdigit(): img[int(a)] = b.strip()

sd = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")
sp, _ = sd.read_with_gaps("arr\\sprites.dat")
def spr(i):
    if i*8+8 > len(sp): return None
    im, x, y, hb, fl = struct.unpack_from("<HBBHH", sp, i*8)
    return im

print("=== overlay breakdown per tileset ===")
for ts in ["badlands","platform","install","ashworld","jungle","desert","ice","twilight"]:
    ng, ids, rem1, d = summary[ts]
    sprite_ov = unit_ov = none = 0
    for eid, recs in d.items():
        k, flags, ov, rem, nm, w, h = recs[0]
        if flags & 0x1000: sprite_ov += 1
        elif flags & 0x2000: unit_ov += 1
        else: none += 1
    print(f"  {ts:9s} ids={len(d):4d}  spriteOverlay={sprite_ov:4d}  unitOverlay={unit_ov:3d}  noOverlay(terrain-only)={none:4d}")

print()
print("=== parent's platform ids 137/256/257: full record + name + GRP ===")
_, _, _, pd = summary["platform"]
for eid in (137, 256, 257):
    k, flags, ov, rem, nm, w, h = pd[eid][0]
    nmtxt = st[nm-1] if 0 < nm <= len(st) else "?"
    grp = ""
    if flags & 0x1000:
        im = spr(ov); grp = img.get(im, "?") if im is not None else "?"
    print(f"  id {eid:4d}: cv5group={k} flags=0x{flags:04x} overlay={ov} name#{nm}='{nmtxt}' w={w} h={h}  GRP={grp or '(none: terrain-only doodad)'}")

print()
print("=== ashworld ids 0..142: name sample ===")
_, _, _, ad = summary["ashworld"]
for eid in (0, 1, 45, 46, 122, 142):
    if eid in ad:
        k, flags, ov, rem, nm, w, h = ad[eid][0]
        nmtxt = st[nm-1] if 0 < nm <= len(st) else "?"
        grp = ""
        if flags & 0x1000:
            im = spr(ov); grp = img.get(im, "?") if im is not None else "?"
        print(f"  id {eid:4d}: flags=0x{flags:04x} name#{nm}='{nmtxt}' w={w} h={h} GRP={grp or '-'}")

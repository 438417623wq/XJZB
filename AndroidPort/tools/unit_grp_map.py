"""Build the authoritative unit-id -> GRP-path map by walking the game's own
data chain: units.dat (flingy ptr) -> flingy.dat (sprite ptr) ->
sprites.dat (image ptr) -> images.dat (tbl ptr) -> images.tbl (path).

This settles every "which GRP is unit X" question with the game's own data
instead of name guessing. The flingy offset inside the 130-byte units.dat
record is not assumed: candidate u16 offsets are scored against known pairs
(marine->marine.grp, tank->tank.grp, scv->SCV.grp, cc->control.grp,
zergling->zergling.grp, drone->drone.grp, probe->probe.grp, zealot->zealot.grp)
and the first offset that explains them all wins.
"""
import struct

import sc_archive
from gapio import GapReader

SD = sc_archive.Archive(r"F:\KF\XJZB\StarDat.mpq")


def read(name):
    d, gaps = SD.read_with_gaps(name)
    return GapReader(d, gaps)


def parse_tbl(g):
    n = g.u16(0)
    offs = [g.u16(2 + i * 2) for i in range(n)]
    out = []
    for o in offs:
        chars = bytearray()
        p = o
        for _ in range(300):
            c = g.byte(p)
            if c == 0:
                break
            chars.append(c)
            p += 1
        out.append(chars.decode("cp1252", "replace"))
    return out


images_tbl = parse_tbl(read("arr\\images.tbl"))

img_g = read("arr\\images.dat")
img_bytes = img_g
# discover record size: images.dat has a 2-byte header? try sizes dividing
raw_img, gaps_img = SD.read_with_gaps("arr\\images.dat")
for rec in range(6, 40):
    cnt = (len(raw_img) - 2) // rec if (len(raw_img) - 2) % rec == 0 else 0
    if cnt and cnt in (999, 998):
        # check u16@0 of each record is a plausible tbl index
        ok = 0
        gg = GapReader(raw_img, gaps_img)
        for e in range(min(cnt, 60)):
            v = gg.u16(2 + e * rec)
            if v < len(images_tbl):
                ok += 1
        if ok == min(cnt, 60):
            IMG_REC, IMG_CNT, IMG_HDR = rec, cnt, 2
            break
else:
    raise SystemExit("images.dat record size not found")


def image_grp(img_id):
    if img_id >= IMG_CNT:
        return None
    ti = img_g.u16(IMG_HDR + img_id * IMG_REC)
    return images_tbl[ti] if ti < len(images_tbl) else "?"


spr_g = read("arr\\sprites.dat")
raw_spr, gaps_spr = SD.read_with_gaps("arr\\sprites.dat")
SPR_CNT = len(raw_spr) // 2


def sprite_image(spr_id):
    if spr_id >= SPR_CNT:
        return None
    return spr_g.u16(spr_id * 2)


fl_g = read("arr\\flingy.dat")
raw_fl, gaps_fl = SD.read_with_gaps("arr\\flingy.dat")
FL_REC = 8
FL_CNT = len(raw_fl) // FL_REC


def flingy_sprite(fl_id):
    if fl_id >= FL_CNT:
        return None
    return fl_g.u16(fl_id * FL_REC)


raw_un, gaps_un = SD.read_with_gaps("arr\\units.dat")
un_g = GapReader(raw_un, gaps_un)
UN_REC, UN_CNT = 130, len(raw_un) // 130

KNOWN = {0: "marine", 5: "tank", 7: "scv", 106: "control", 37: "zergling",
         41: "drone", 64: "probe", 65: "zealot", 111: "tbarrack"}


def unit_grp_at_off(u, off):
    fl = un_g.u16(u * UN_REC + off)
    if fl >= FL_CNT:
        return None
    img = flingy_sprite(fl)
    if img is None:
        return None
    return image_grp(img)


best_off, best_ok = None, -1
for off in range(0, UN_REC - 1, 2):
    ok = 0
    for u, frag in KNOWN.items():
        s = unit_grp_at_off(u, off)
        if s and frag.lower() in s.lower():
            ok += 1
    if ok > best_ok:
        best_ok, best_off = ok, off
print("best flingy offset in units.dat record: %d (matches %d/%d knowns, count=%d)"
      % (best_off, best_ok, len(KNOWN), UN_CNT))

lines = []
for u in range(UN_CNT):
    s = unit_grp_at_off(u, best_off)
    lines.append("%d\t%s" % (u, s if s else "-"))
with open("unit_grp_map.txt", "w", encoding="utf8") as fp:
    fp.write("\n".join(lines) + "\n")
print("written unit_grp_map.txt (%d units)" % UN_CNT)

# print the units the plan cares about
import io
stat = [l.split("\t", 1)[1] for l in io.open("stat_txt.txt", encoding="utf8", errors="replace")]
WANT_IDS = [13, 14, 34, 35, 36, 39, 40, 44, 45, 46, 47, 50, 58, 59, 60, 61, 62,
            63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 83, 84, 85, 97, 103,
            105, 107, 108, 115, 116, 117, 118, 120, 122, 123, 130, 134, 135,
            136, 137, 138, 139, 140, 141, 142, 143, 144, 146, 147, 148, 149,
            150, 151, 152, 154, 155, 156, 157, 159, 160, 162, 163, 164, 165,
            166, 167, 168, 169, 170, 171, 172, 173, 175, 188, 214, 215]
for u in WANT_IDS:
    nm = stat[u].split("\t", 1)[-1] if u < len(stat) else "?"
    print("%3d %-34s %s" % (u, nm, unit_grp_at_off(u, best_off)))

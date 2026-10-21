"""v2.11 batch B: recover the sprites.dat stride by pinning it to known pairs.

Six zerg buildings already ship and are provably right, so their units.dat id and
their images.tbl index are both known:

    131 Hatchery -> zerg\\hatchery.grp  (image 77)
    141 Spire    -> zerg\\spire.grp     (image 115)
    142 Pool     -> zerg\\Snakey.grp    (image 112)
    143 Creep    -> zerg\\fcolony.grp   (image 74)
    146 Sunken   -> zerg\\SColony.grp   (image 118)
    149 Extract  -> zerg\\Extract.grp   (image 108)

sprites.dat is stored in units.dat order, so sprites.dat[id * stride + offset]
should equal the image index. That is six simultaneous constraints on
(stride, offset), which pins both exactly -- and once pinned, the same read
answers Hydralisk Den 135, Defiler Mound 136, Queen's Nest 138, Evolution
Chamber 139 and Ultralisk Cavern 140.

Usage: python probe_v211y.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sc_archive

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))
BD = sc_archive.Archive(os.path.join(ROOT, "BrooDat.mpq"))
PT = sc_archive.Archive(os.path.join(ROOT, "patch_rt.mpq"))

PAIRS = [
    (131, "zerg\\hatchery.grp"),
    (141, "zerg\\spire.grp"),
    (142, "zerg\\Snakey.grp"),
    (143, "zerg\\fcolony.grp"),
    (146, "zerg\\SColony.grp"),
    (149, "zerg\\Extract.grp"),
    (150, "zerg\\chrysal.grp"),
    (134, "zerg\\NydusPit.grp"),
]
# the ones we actually want to resolve
WANT = [135, 136, 137, 138, 139, 140, 132, 133, 144, 147, 151, 152]


def read(path, order=(BD, PT, SD)):
    for ar in order:
        if ar.has(path):
            data, _ = ar.read_with_gaps(path)
            return data
    return None


def read_tbl(data):
    count = data[0] | (data[1] << 8)
    offs = [(data[2 + i * 2] | (data[3 + i * 2] << 8)) for i in range(count)]
    out = []
    for off in offs:
        if off >= len(data):
            out.append("")
            continue
        end = data.find(b"\x00", off)
        out.append(data[off:end].decode("cp1252", "replace") if end > 0 else "")
    return out


def u16(d, o):
    return d[o] | (d[o + 1] << 8)


for tag, ar in (("StarDat", SD), ("BrooDat", BD)):
    imt = read("arr\\images.tbl", order=(ar,))
    spr = read("arr\\sprites.dat", order=(ar,))
    if imt is None or spr is None:
        print("%s: missing images.tbl or sprites.dat" % tag)
        continue
    images = read_tbl(imt)
    # normalise: images.tbl paths have no leading "unit\" but the archives do
    lut = {}
    for i, p in enumerate(images):
        lut.setdefault(p.lower().replace("/", "\\"), i)
    print("=== %s  images.tbl=%d entries  sprites.dat=%d bytes ===" % (tag, len(images), len(spr)))

    targets = []
    for uid, path in PAIRS:
        idx = lut.get(path.lower())
        if idx is None:
            print("  cannot locate %s in images.tbl" % path)
            continue
        targets.append((uid, idx, path))
    if len(targets) < 4:
        print("  too few anchors")
        continue

    hits = []
    for R in range(2, 65):
        for O in range(0, R):
            if all(O + uid * R + 2 <= len(spr) and u16(spr, O + uid * R) == idx
                   for uid, idx, _ in targets):
                hits.append((R, O))
    print("  stride/offset hits: %s" % hits)

    for R, O in hits[:2]:
        print("  --- stride=%d offset=%d ---" % (R, O))
        for uid, idx, path in targets:
            print("      %3d -> %4d  %s  (ok)" % (uid, u16(spr, O + uid * R), path))
        for uid in WANT:
            off = O + uid * R
            if off + 2 > len(spr):
                continue
            v = u16(spr, off)
            print("      %3d -> %4d  %s" % (uid, v, images[v] if v < len(images) else "<<oob>>"))

"""Validate StarCraft.exe 0x10674e stride=32 sub=1: map DD2 ids -> sprite ->
tileset must match the map's tileset. Also hexdump a few entries."""
import os
import struct
import sys

import sc_archive
from gapio import GapReader

ROOT = r"F:\KF\XJZB"
SD = sc_archive.Archive(os.path.join(ROOT, "StarDat.mpq"))


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


images_tbl = parse_tbl(read(r"arr\images.tbl"))
spr_g = read(r"arr\sprites.dat")
d, _ = SD.read_with_gaps(r"arr\sprites.dat")
sprite_image = [spr_g.u16(i * 2) for i in range(len(d) // 2)]


def sprite_name(s):
    if s >= len(sprite_image):
        return None
    e = sprite_image[s]
    if e >= len(images_tbl):
        return None
    return images_tbl[e]


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_maps as pm

TILESETS = pm.TILESETS
import collections
used = collections.defaultdict(set)
for src, mid in [("maps\\(4)Blood Bath.scm", "bloodbath"),
                 ("maps\\(2)Bottleneck.scm", "bottleneck"),
                 ("maps\\(2)Boxer.scm", "boxer"),
                 ("maps\\(4)Dark Crystal.scm", "darkcrystal"),
                 ("maps\\(3)Three Kingdoms.scm", "3kingdoms"),
                 ("maps\\(2)The Small Divide.scm", "divide"),
                 ("maps\\(4)Cyclone.scm", "cyclone"),
                 ("maps\\(2)Volcanis.scm", "volcanis"),
                 ("maps\\(2)River Crossing.scm", "river")]:
    r = pm.read_chk(os.path.join(pm.ROOT, src))
    if not r:
        continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    key = b"DD2 " if b"DD2 " in sec else b"DDDATA"
    if key not in sec:
        continue
    off, size = sec[key]
    for k in range(size // 8):
        used[mid].add(struct.unpack_from("<H", chk, off + k * 8)[0])

BASE, STRIDE, SUB = 0x10674E, 32, 1
blob = open(os.path.join(ROOT, "StarCraft.exe"), "rb").read()
tot = tmatch = anydoodad = 0
per_map = []
for mid, ids in sorted(used.items()):
    ts = TILESETS.get(mid)
    mok = mtot = 0
    for v in sorted(ids):
        p = BASE + v * STRIDE + SUB
        if p + 2 > len(blob):
            continue
        s = struct.unpack_from("<H", blob, p)[0]
        nm = sprite_name(s)
        mtot += 1
        tot += 1
        if nm and nm.lower().startswith("thingy\\tileset\\"):
            anydoodad += 1
            mok += 1
            if ts and ("\\" + ts.lower() + "\\") in nm.lower():
                tmatch += 1
    per_map.append("%s=%d/%d" % (mid, mok, mtot))
print("doodad-art=%d/%d tileset-match=%d" % (anydoodad, tot, tmatch))
print(" ".join(per_map))

print("--- raw entries 0-3, 60-62 ---")
for k in [0, 1, 2, 3, 60, 61, 62]:
    p = BASE + k * STRIDE
    e = blob[p - 4:p + STRIDE + 4]
    print("k=%-3d %s" % (k, e.hex(" ")))

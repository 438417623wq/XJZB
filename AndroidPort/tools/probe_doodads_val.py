"""Validate the exe doodads.dat candidate (offset, stride) against every map:
for each DD2 record, entry[k].sprite -> grp name; the grp's tileset folder
must equal the map's tileset (or be a marker/generic). Prints per-candidate
match rates so the real table wins unambiguously.
"""
import os
import struct
import collections

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


import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_maps as pm

MAPS = [
    ("maps\\(4)Blood Bath.scm", "bloodbath", "platform"),
    ("maps\\(2)Bottleneck.scm", "bottleneck", "ashworld"),
    ("maps\\(2)Boxer.scm", "boxer", "platform"),
    ("maps\\(8)The Hunters.scm", "hunters", "jungle"),
    ("maps\\(4)Dark Crystal.scm", "darkcrystal", "ashworld"),
    ("maps\\(3)Three Kingdoms.scm", "3kingdoms", "badlands"),
    ("maps\\(2)The Small Divide.scm", "divide", "jungle"),
    ("maps\\(4)Cyclone.scm", "cyclone", "ashworld"),
    ("maps\\(2)Volcanis.scm", "volcanis", "ashworld"),
    ("maps\\(2)River Crossing.scm", "river", "jungle"),
]

# collect DD2 ids per map with the map's real tileset (from pipeline_maps TILESETS)
TILESETS = getattr(pm, "TILESETS", {})
dd_ids = {}
for src, mid, _guess in MAPS:
    r = pm.read_chk(os.path.join(pm.ROOT, src))
    if not r:
        continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    key = b"DD2 " if b"DD2 " in sec else b"DDDATA"
    if key not in sec:
        continue
    off, size = sec[key]
    ids = set()
    for k in range(size // 8):
        v, x, y, owner, pct = struct.unpack_from("<HHHBB", chk, off + k * 8)
        ids.add(v)
    real_ts = TILESETS.get(mid)
    dd_ids[mid] = (ids, real_ts)

for exe, cands in [("StarEdit.exe", [(0x9D980, 36), (0x9D980, 32), (0x6F910, 30), (0x6FB50, 28)]),
                   ("StarCraft.exe", [(0x106E60, 32), (0x10E090, 36), (0x10E0B0, 30), (0x106EA0, 16)])]:
    blob = open(os.path.join(ROOT, exe), "rb").read()
    for off, stride in cands:
        tot = ok = 0
        tileset_ok = 0
        per_map = []
        for mid, (ids, real_ts) in dd_ids.items():
            mok = mtot = 0
            for v in ids:
                e = off + v * stride
                if e + 2 > len(blob):
                    continue
                s = struct.unpack_from("<H", blob, e)[0]
                nm = sprite_name(s)
                tot += 1
                mtot += 1
                if nm and nm.lower().startswith("thingy\\tileset\\"):
                    ok += 1
                    mok += 1
                    if real_ts and ("\\" + real_ts.lower() + "\\") in nm.lower():
                        tileset_ok += 1
            per_map.append("%s %d/%d" % (mid, mok, mtot))
        print("%s off=0x%06x stride=%d  doodad-sprite=%d/%d  tileset-match=%d  %s"
              % (exe, off, stride, ok, tot, tileset_ok, " ".join(per_map)))

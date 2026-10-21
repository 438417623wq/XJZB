"""Validate the corrected-scan candidates against map DD2 ground truth:
entry[v] (sprite field) must resolve to doodad art from the map's own tileset
folder (special/neutral ids exempt: they may use marker/flag art)."""
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

print("pipeline_maps TILESETS:", getattr(pm, "TILESETS", "ABSENT"))
TILESETS = getattr(pm, "TILESETS", {})

import collections
used = collections.defaultdict(set)   # mid -> ids
for src, mid in [("maps\\(4)Blood Bath.scm", "bloodbath"),
                 ("maps\\(2)Bottleneck.scm", "bottleneck"),
                 ("maps\\(2)Boxer.scm", "boxer"),
                 ("maps\\(8)The Hunters.scm", "hunters"),
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

CANDS = [
    ("StarEdit.exe", 0x5FE88, 28, 0), ("StarEdit.exe", 0x5FE7C, 28, 12),
    ("StarEdit.exe", 0x5D67C, 28, 4), ("StarEdit.exe", 0x5AE78, 28, 0),
    ("StarCraft.exe", 0x1193B4, 24, 2), ("StarCraft.exe", 0x118380, 24, 6),
]
blobs = {}
for exe, base, stride, sub in CANDS:
    blob = blobs.setdefault(exe, open(os.path.join(ROOT, exe), "rb").read())
    tot = tmatch = anydoodad = 0
    for mid, ids in used.items():
        ts = TILESETS.get(mid)
        for v in ids:
            p = base + v * stride + sub
            if p + 2 > len(blob):
                continue
            s = struct.unpack_from("<H", blob, p)[0]
            nm = sprite_name(s)
            tot += 1
            if nm and nm.lower().startswith("thingy\\tileset\\"):
                anydoodad += 1
                if ts and ("\\" + ts.lower() + "\\") in nm.lower():
                    tmatch += 1
    print("%-13s base=0x%06x stride=%2d sub=%2d  doodad-art=%3d/%3d  tileset-match=%3d"
          % (exe, base, stride, sub, anydoodad, tot, tmatch))

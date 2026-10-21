"""Validate the scan-found doodads.dat candidates by tileset match against
real DD2 placements from the bundled maps."""
import os
import struct
import sys

import numpy as np

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

TILESETS = getattr(pm, "TILESETS", {})
MAPS = [
    ("maps\\(4)Blood Bath.scm", "bloodbath"),
    ("maps\\(2)Bottleneck.scm", "bottleneck"),
    ("maps\\(2)Boxer.scm", "boxer"),
    ("maps\\(8)The Hunters.scm", "hunters"),
    ("maps\\(4)Dark Crystal.scm", "darkcrystal"),
    ("maps\\(3)Three Kingdoms.scm", "3kingdoms"),
    ("maps\\(2)The Small Divide.scm", "divide"),
    ("maps\\(4)Cyclone.scm", "cyclone"),
    ("maps\\(2)Volcanis.scm", "volcanis"),
    ("maps\\(2)River Crossing.scm", "river"),
]
dd = {}
for src, mid in MAPS:
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
        v = struct.unpack_from("<H", chk, off + k * 8)[0]
        ids.add(v)
    dd[mid] = (ids, TILESETS.get(mid))

CANDS = [
    ("StarEdit.exe", 0x9F0CC, 28, 0), ("StarEdit.exe", 0x9F150, 28, 8),
    ("StarEdit.exe", 0x9F234, 28, 24), ("StarEdit.exe", 0x9F248, 28, 4),
    ("StarEdit.exe", 0x9F29C, 28, 14), ("StarEdit.exe", 0x9F6C4, 24, 10),
    ("StarEdit.exe", 0x9F700, 24, 10),
    ("StarCraft.exe", 0x110578, 26, 8), ("StarCraft.exe", 0x110580, 26, 0),
]
blobs = {}
for exe, base, stride, sub in CANDS:
    blob = blobs.setdefault(exe, open(os.path.join(ROOT, exe), "rb").read())
    tot = tmatch = 0
    det = []
    for mid, (ids, ts) in dd.items():
        mok = mtot = 0
        for v in ids:
            p = base + v * stride + sub
            if p + 2 > len(blob):
                continue
            s = struct.unpack_from("<H", blob, p)[0]
            nm = sprite_name(s)
            mtot += 1
            tot += 1
            if nm and nm.lower().startswith("thingy\\tileset\\"):
                mok += 1
                if ts and ("\\" + ts.lower() + "\\") in nm.lower():
                    tmatch += 1
        det.append("%s %d/%d" % (mid, mok, mtot))
    print("%-13s base=0x%06x stride=%2d sub=%2d  sprite=%3d/%d tileset=%3d  %s"
          % (exe, base, stride, sub, sum(1 for _ in []), tot, tmatch, " ".join(det)))

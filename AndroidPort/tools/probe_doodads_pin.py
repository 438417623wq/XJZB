"""Pin the doodads.dat layout from ground truth: for a handful of DD2 ids
whose correct art tileset we KNOW (from the map they appear on), find every
(base, stride, sub) in the exe where entry[v] holds a sprite of THAT tileset;
intersect the constraints across ids of DIFFERENT tilesets.
"""
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


# tileset -> set of sprite ids whose art is from that tileset folder
ts_sprites = {}
for s, e in enumerate(sprite_image):
    if e < len(images_tbl):
        low = images_tbl[e].lower()
        if low.startswith("thingy\\tileset\\"):
            ts = low.split("\\")[2]
            ts_sprites.setdefault(ts, set()).add(s)

# ground-truth (id -> tileset) pairs from maps, chosen to span tilesets
GT = [
    # (dd2 id, tileset, map)
    (62, "ashworld", "cyclone"), (79, "ashworld", "cyclone"),
    (89, "ashworld", "cyclone"), (103, "ashworld", "cyclone"),
    (91, "badlands", "3kingdoms"), (106, "badlands", "3kingdoms"),
    (95, "badlands", "3kingdoms"), (107, "badlands", "3kingdoms"),
    (185, "jungle", "river"), (186, "jungle", "river"),
    (180, "jungle", "river"), (96, "jungle", "river"),
    (111, "platform", "boxer"), (79, "platform", "boxer"),  # 79 in both!
    (112, "platform", "boxer"), (40, "platform", "boxer"),
    (21, "ashworld", "volcanis"), (25, "ashworld", "volcanis"),
]
# note: id 79 appears on both cyclone(ash) and boxer(platform) -- that single
# fact alone REFUTES a global id->sprite table; keep it to observe.

for exe in ("StarEdit.exe", "StarCraft.exe"):
    blob = open(os.path.join(ROOT, exe), "rb").read()
    print("--- %s ---" % exe)
    # positions where each tileset's sprites occur
    ts_pos = {}
    all_pos = []
    for p in range(0, len(blob) - 1):
        s = blob[p] | (blob[p + 1] << 8)
        for ts, ids in ts_sprites.items():
            if s in ids:
                ts_pos.setdefault(ts, []).append(p)
    for ddid, ts, m in GT:
        cands = ts_pos.get(ts, [])
        # positions p such that p == base + ddid*stride + sub for the scan grid
        print("  id=%3d %-9s (%s): %d tileset-sprite positions in exe" %
              (ddid, ts, m, len(cands)))

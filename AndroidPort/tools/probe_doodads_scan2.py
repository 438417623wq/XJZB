"""Constrained scan over the dense exe regions: find (base, stride, sub)
where map-used DD2 ids land on entries containing a sprite of the map's OWN
tileset. DD2 ids are tileset-local (id 79 appears on both an ashworld and a
platform map), so the exe table -- if it is one flat array indexed by id --
would contradict that; the scan will tell us.
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

ts_sprites = {}
for s, e in enumerate(sprite_image):
    if e < len(images_tbl):
        low = images_tbl[e].lower()
        if low.startswith("thingy\\tileset\\"):
            ts = low.split("\\")[2]
            ts_sprites.setdefault(ts, set()).add(s)

GT = [
    (62, "ashworld"), (79, "ashworld"), (89, "ashworld"), (103, "ashworld"),
    (91, "badlands"), (106, "badlands"), (95, "badlands"), (107, "badlands"),
    (185, "jungle"), (186, "jungle"), (180, "jungle"), (96, "jungle"),
    (111, "platform"), (112, "platform"), (40, "platform"), (35, "platform"),
    (21, "ashworld"), (25, "ashworld"), (3, "ashworld"),
]

for exe, lo, hi in (("StarEdit.exe", 0x9D000, 0xA3000),
                    ("StarCraft.exe", 0x10E000, 0x113000)):
    blob = open(os.path.join(ROOT, exe), "rb").read()
    seg = np.frombuffer(blob[lo:hi], dtype=np.uint8)
    vals = seg[:-1].astype(np.uint32) | (seg[1:].astype(np.uint32) << 8)
    print("--- %s seg 0x%x-0x%x ---" % (exe, lo, hi))
    results = []
    for stride in (28, 30, 32, 34, 36, 38, 40):
        for sub in range(0, stride, 2):
            maxb = len(seg) - (287 * stride + sub + 2)
            if maxb <= 0:
                continue
            for base in range(0, maxb, 4):
                score = 0
                for v, ts in GT:
                    p = base + v * stride + sub
                    if p + 1 >= len(seg):
                        continue
                    s = int(seg[p]) | (int(seg[p + 1]) << 8)
                    if s in ts_sprites.get(ts, ()):
                        score += 1
                if score >= 10:
                    results.append((score, lo + base, stride, sub))
    results.sort(reverse=True)
    for r in results[:10]:
        print("  score=%d/%d base=0x%06x stride=%d sub=%d" % (r[0], len(GT), r[1], r[2], r[3]))
    if not results:
        print("  (no candidate scores >= 10)")

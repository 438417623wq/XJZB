"""Study dddata.bin structure. The heads are (n, n+1) u16 pairs -- test
whether those values are SPRITE ids of the same tileset's doodad art, and
map the whole file: where do tileset-sprite ids occur, what do the zeros
separate, and is there a fixed record size.
"""
import os

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
sprite_ts = {}
for s, e in enumerate(sprite_image):
    if e < len(images_tbl):
        low = images_tbl[e].lower()
        if low.startswith("thingy\\tileset\\"):
            ts = low.split("\\")[2]
            ts_sprites.setdefault(ts, set()).add(s)
            sprite_ts[s] = ts

print("sprites per tileset:")
for ts in sorted(ts_sprites):
    print("  %-9s %s" % (ts, sorted(ts_sprites[ts])))

for ts in ("ashworld", "badlands", "jungle", "platform", "install"):
    d, gaps = SD.read_with_gaps("tileset\\%s\\dddata.bin" % ts)
    arr = np.frombuffer(d, dtype=np.uint8)
    vals = arr[:-1].astype(np.uint32) | (arr[1:].astype(np.uint32) << 8)
    hits = [(p, int(v)) for p, v in enumerate(vals) if v in ts_sprites.get(ts, ())]
    print("--- %s: size=%d, tileset-sprite-id hits=%d ---" % (ts, len(d), len(hits)))
    print("   first 40 hits:", hits[:40])

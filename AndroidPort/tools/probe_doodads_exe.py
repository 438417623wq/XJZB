"""Locate the exe-side doodads.dat (ddID -> sprite) inside StarEdit.exe /
StarCraft.exe and validate it against every bundled map's DD2 placements.

Chain: sprites.dat[u16] -> image id; images.tbl[image] -> grp name.
Doodad sprites are the ones whose grp name starts with "thingy\\tileset\\".
The exe table should be a fixed-stride array whose entries hold such sprite
ids; each DD2 record's u16 id indexes it. Validation: the entry's tileset
folder must match the map's tileset.
"""
import os
import struct

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
n_spr = len(d) // 2
sprite_image = [spr_g.u16(i * 2) for i in range(n_spr)]


def sprite_name(s):
    if s is None or s >= n_spr:
        return None
    e = sprite_image[s]
    if e is None or e >= len(images_tbl):
        return None
    return images_tbl[e]


doodad_sprites = {}
for s in range(n_spr):
    nm = sprite_name(s)
    if nm and nm.lower().startswith("thingy\\tileset\\"):
        doodad_sprites[s] = nm
print("sprites=%d, doodad sprites=%d" % (n_spr, len(doodad_sprites)))
svals = sorted(doodad_sprites)
print("sprite id range: %d..%d" % (svals[0], svals[-1]))

# scan the exes for dense runs of doodad sprite ids at various strides
for exe in [r"StarEdit.exe", r"StarCraft.exe", r"brood.dll", r"storm.dll"]:
    p = os.path.join(ROOT, exe)
    if not os.path.exists(p):
        continue
    blob = open(p, "rb").read()
    print("--- %s (%d bytes) ---" % (exe, len(blob)))
    for stride in (36, 32, 30, 28, 24, 20, 16):
        best = None
        # slide: count u16 positions where value is a doodad sprite id
        for off in range(0, len(blob) - 288 * stride, 0x10):
            hits = 0
            for k in range(288):
                v = struct.unpack_from("<H", blob, off + k * stride)[0]
                if v in doodad_sprites:
                    hits += 1
            if hits >= 200:
                if best is None or hits > best[1]:
                    best = (off, hits)
        if best:
            print("  stride=%d  off=0x%x  hits=%d/288" % (stride, best[0], best[1]))

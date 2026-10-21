"""Exhaustive 3-parameter scan for the exe-embedded doodads.dat:
(base, stride, sprite-sub-offset) such that most of the 288 entries hold a
doodad-sprite u16, then validated by tileset match against real DD2 data.

Doodad sprites: sprites.dat -> image -> images.tbl name starting with
"thingy\\tileset\\".
"""
import os
import struct

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

doodad = np.zeros(65536, dtype=np.uint8)
for s, e in enumerate(sprite_image):
    if e < len(images_tbl) and images_tbl[e].lower().startswith("thingy\\tileset\\"):
        if s != 0:
            doodad[s] = 1
print("doodad sprite ids:", int(doodad.sum()))

N = 288
for exe in ("StarEdit.exe", "StarCraft.exe"):
    blob = np.frombuffer(open(os.path.join(ROOT, exe), "rb").read(), dtype=np.uint8)
    bit = doodad[blob.astype(np.uint32)]  # per-byte -> whether the u16 STARTING here is doodad? need pairs
    # u16 value at pos p = blob[p] | blob[p+1]<<8; build per-position flag
    vals = blob[:-1].astype(np.uint32) | (blob[1:].astype(np.uint32) << 8)
    flag = doodad[vals]
    flag = np.concatenate([flag, [0]])
    csum = np.concatenate([[0], np.cumsum(flag)])
    print("--- %s ---" % exe)
    results = []
    for stride in range(24, 45, 2):
        for sub in range(0, stride):
            maxb = len(blob) - (N - 1) * stride - sub - 2
            if maxb <= 0:
                continue
            bases = np.arange(0, maxb, 2)
            cnt = np.zeros(len(bases), dtype=np.int32)
            for k in range(N):
                cnt += flag[bases + k * stride + sub]
            top = np.argsort(cnt)[-3:]
            for t in top:
                if cnt[t] >= N * 0.6:
                    results.append((int(cnt[t]), int(bases[t]), stride, sub))
    results.sort(reverse=True)
    seen = set()
    for cnt, base, stride, sub in results[:12]:
        key = (base // 64, stride)
        if key in seen:
            continue
        seen.add(key)
        print("  count=%3d/288 base=0x%06x stride=%d sub=%d" % (cnt, base, stride, sub))

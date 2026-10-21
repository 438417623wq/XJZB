"""v2.44: find which hydra.grp frame block is the real death explosion.

pipeline_sprites.py ANIMS has death_hydra = ("unit\\zerg\\hydra.grp", 17 * 17),
i.e. block 17 (frames 289..305).  The art audit claims that block is blank and
the explosion lives in block 12 (frames 204..220).  Measure every block so the
fix is not a guess.
"""
import os
import sys

import numpy as np

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import grp as grpm
import pipeline_sprites as ps

print("loading hydra.grp ...")
res = ps.load_grp(r"unit\zerg\hydra.grp")
if res is None:
    raise SystemExit("hydra.grp not found in any archive")
frames, mw, mh = res
print("frames=%d maxW=%d maxH=%d" % (len(frames), mw, mh))
print()
print("block  frames      nonEmpty  meanRGB            red  redPix  maxSize")
for b in range(len(frames) // 17 + 1):
    lo, hi = b * 17, min(len(frames), (b + 1) * 17)
    if lo >= hi:
        break
    ne = 0
    rs = gs = bs = 0
    red = 0
    redpix = 0
    big = (0, 0)
    for fi in range(lo, hi):
        f = frames[fi]
        px = np.frombuffer(bytes(f["px"]), dtype=np.uint8).reshape(f["h"], f["w"])
        mask = px != 255
        c = int(mask.sum())
        if c:
            ne += 1
        pal = np.array(ps.BASE_PAL, dtype=np.int32)
        rgb = pal[px]
        rs += int(rgb[:, :, 0][mask].sum())
        gs += int(rgb[:, :, 1][mask].sum())
        bs += int(rgb[:, :, 2][mask].sum())
        r = int(((rgb[:, :, 0] > 120) & (rgb[:, :, 0] > rgb[:, :, 1] + 40) & mask).sum())
        if r:
            red += 1
            redpix += r
        if f["w"] * f["h"] > big[0] * big[1]:
            big = (f["w"], f["h"])
    tot = sum(f["w"] * f["h"] for f in frames[lo:hi])
    if tot == 0:
        continue
    print("  %-3d  %3d..%-3d  %8d  (%5.1f,%5.1f,%5.1f)  %3d  %6d  %dx%d"
          % (b, lo, hi - 1, ne, rs / max(1, tot), gs / max(1, tot), bs / max(1, tot),
             red, redpix, big[0], big[1]))

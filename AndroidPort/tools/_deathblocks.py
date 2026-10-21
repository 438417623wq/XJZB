"""v2.44: same block measurement for marine.grp and zergling.grp, to check that
death_marine = 13*17 and death_zergling = 17*17 (the entries the audit says are
correct) really do point at their explosions."""
import sys

import numpy as np

sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_sprites as ps

for path, claim in ((r"unit\terran\marine.grp", 13),
                    (r"unit\zerg\zergling.grp", 17),
                    (r"unit\terran\firebat.grp", None)):
    res = ps.load_grp(path)
    if res is None:
        print(path, "NOT FOUND")
        continue
    frames, mw, mh = res
    pal = np.array(ps.BASE_PAL, dtype=np.int32)
    print("== %s  frames=%d  maxW=%d maxH=%d   (ANIMS claims block %s)"
          % (path, len(frames), mw, mh, claim))
    print("   block  frames       nonEmpty  meanRGB            redPix  maxSize")
    for b in range(len(frames) // 17 + 1):
        lo, hi = b * 17, min(len(frames), (b + 1) * 17)
        if lo >= hi:
            break
        ne = 0
        rs = gs = bs = 0
        redpix = 0
        big = (0, 0)
        tot = 0
        for fi in range(lo, hi):
            f = frames[fi]
            px = np.frombuffer(bytes(f["px"]), dtype=np.uint8).reshape(f["h"], f["w"])
            mask = px != 255
            tot += f["w"] * f["h"]
            if mask.any():
                ne += 1
            rgb = pal[px]
            rs += int(rgb[:, :, 0][mask].sum())
            gs += int(rgb[:, :, 1][mask].sum())
            bs += int(rgb[:, :, 2][mask].sum())
            redpix += int(((rgb[:, :, 0] > 120) & (rgb[:, :, 0] > rgb[:, :, 1] + 40)
                           & mask).sum())
            if f["w"] * f["h"] > big[0] * big[1]:
                big = (f["w"], f["h"])
        if tot == 0:
            continue
        print("   %-5d  %3d..%-3d  %8d  (%5.1f,%5.1f,%5.1f)  %6d  %dx%d"
              % (b, lo, hi - 1, ne, rs / tot, gs / tot, bs / tot, redpix,
                 big[0], big[1]))
    print()

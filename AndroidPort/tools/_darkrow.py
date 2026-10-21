# v2.42: hunt for THIN dark rows inside terrain chunks.
# The reported bar is only ~36 screen px tall, i.e. ~28 world px at zoom 1.3 --
# far thinner than a 512px chunk. If each chunk carried one dark row at a
# DIFFERENT y, the screen would show a full-width dark band that steps up/down
# by half a tile at every chunk-column boundary, which is exactly the geometry
# in the v2.42 write-up. The earlier >=95%-of-width test was too strict to see
# a partial dark row, so this pass records the darkest row of every chunk and
# its offset.
import os
import numpy as np
from PIL import Image

root = r"F:/KF/XJZB/AndroidPort/app/app/src/main/assets/maps"
hits = []
permap = {}
n = 0
for mid in sorted(os.listdir(root)):
    d = os.path.join(root, mid)
    if not os.path.isdir(d):
        continue
    for fn in sorted(os.listdir(d)):
        if not (fn.startswith("c_") and fn.endswith(".webp")):
            continue
        a = np.asarray(Image.open(os.path.join(d, fn)).convert("L")).astype(np.float32)
        n += 1
        rm = a.mean(axis=1)
        i = int(rm.argmin())
        mn = float(rm[i])
        if mn < 25.0:
            hits.append((mid + "/" + fn, round(mn, 1), i, round(float(np.median(rm)), 1)))
            permap.setdefault(mid, []).append(i)

print("scanned", n)
print("chunks with a row darker than 25:", len(hits))
print("maps affected:", len(permap))
for mid in sorted(permap):
    ys = sorted(permap[mid])
    print("  %-18s n=%-3d rowY=%s" % (mid, len(ys), ys[:24]))

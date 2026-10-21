# v2.42: scan every shipped terrain chunk for near-black ROWS / COLUMNS.
# A static black row at a chunk edge would print as a full-width bar whose
# spacing equals the chunk row pitch -- exactly the reported geometry. The
# [v242] asset gate only counts total black pixels against a baseline, so a
# thin black row inside an otherwise-dark map slips through it.
import os
import numpy as np
from PIL import Image

root = r"F:/KF/XJZB/AndroidPort/app/app/src/main/assets/maps"
rows = []
cols = []
darkchunks = []
n = 0
for mid in sorted(os.listdir(root)):
    d = os.path.join(root, mid)
    if not os.path.isdir(d):
        continue
    for fn in sorted(os.listdir(d)):
        if not (fn.startswith("c_") and fn.endswith(".webp")):
            continue
        p = os.path.join(d, fn)
        im = Image.open(p).convert("RGB")
        a = np.asarray(im).astype(np.int16)
        n += 1
        H, W = a.shape[0], a.shape[1]
        dark = (a < 8).all(axis=2)
        rc = dark.sum(axis=1)
        bad = np.where(rc >= W * 0.95)[0]
        if bad.size:
            rows.append((mid + "/" + fn, H, W, int(bad.size), int(bad[0]), int(bad[-1])))
        cc = dark.sum(axis=0)
        badc = np.where(cc >= H * 0.95)[0]
        if badc.size:
            cols.append((mid + "/" + fn, int(badc.size), int(badc[0]), int(badc[-1])))
        if dark.mean() > 0.5:
            darkchunks.append((mid + "/" + fn, round(float(dark.mean()), 3), H, W))

print("scanned", n)
print("rows >=95%% near-black:", len(rows))
for r in rows[:80]:
    print("  ROW", r)
print("cols >=95%% near-black:", len(cols))
for r in cols[:60]:
    print("  COL", r)
print("chunks >50%% near-black:", len(darkchunks))
for r in darkchunks[:60]:
    print("  DARK", r)

"""v2.42 收尾: 像素级 diff —— v2.41 APK 内的地形 chunk vs 当前磁盘上的 v2.42 chunk。

预期: 只有含 void 碎块的图发生变化, 且每图变化像素数量级为数百~数千;
crusader / newgettysburg 等黑海图的**黑海区域必须逐字节不变**(v2 规则只填 <=64 格的碎块)。
"""
import io
import os
import zipfile

import numpy as np
from PIL import Image

APK = r"F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk"
DISK = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps"

z = zipfile.ZipFile(APK)
rows = []
identical = changed = missing = 0

names = [n for n in z.namelist()
         if n.startswith("assets/maps/") and n.endswith(".webp")
         and os.path.basename(n).startswith("c_")]

for name in names:
    mid = name.split("/")[2]
    fn = name.split("/")[-1]
    disk = os.path.join(DISK, mid, fn)
    if not os.path.exists(disk):
        missing += 1
        continue
    a = np.asarray(Image.open(io.BytesIO(z.read(name))).convert("RGB"), dtype=np.uint8)
    b = np.asarray(Image.open(disk).convert("RGB"), dtype=np.uint8)
    if a.shape != b.shape:
        rows.append((mid, fn, -1, "SHAPE %s vs %s" % (a.shape, b.shape)))
        changed += 1
        continue
    diff = np.any(a != b, axis=2)
    n = int(diff.sum())
    if n == 0:
        identical += 1
        continue
    changed += 1
    # 变黑的像素: v2.41 有颜色, v2.42 变纯黑 —— 绝不允许出现
    b_black = np.all(b < 8, axis=2)
    a_lit = np.any(a > 16, axis=2)
    darker = int((b_black & a_lit).sum())
    # 变亮的像素: 黑 -> 地形 (本轮修复的正是这一类)
    a_black = np.all(a < 8, axis=2)
    b_lit = np.any(b > 16, axis=2)
    lighter = int((a_black & b_lit).sum())
    rows.append((mid, fn, n, "fixed=%d regressed=%d" % (lighter, darker)))

print("identical %d changed %d missing %d" % (identical, changed, missing))
rows.sort(key=lambda r: -r[2])
print("%-18s %-14s %10s  %s" % ("map", "chunk", "px", "note"))
for mid, fn, n, note in rows[:40]:
    print("%-18s %-14s %10d  %s" % (mid, fn, n, note))
if len(rows) > 40:
    print("... %d more changed chunks" % (len(rows) - 40))

per_map = {}
for mid, fn, n, note in rows:
    if n > 0:
        per_map[mid] = per_map.get(mid, 0) + n
print("--- per-map changed px ---")
for mid, n in sorted(per_map.items(), key=lambda kv: -kv[1]):
    print("%-18s %d" % (mid, n))

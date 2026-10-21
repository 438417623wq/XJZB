from PIL import Image
import statistics

im = Image.open(r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\ceb98bc41cacc4d5590282f1cebdd421.jpg').convert('RGB')
W, H = im.size
px = im.load()
# crystal blue pixels: high blue, moderate green, low red
pts = []
for y in range(300, 1200):
    for x in range(600, 1900):
        r, g, b = px[x, y]
        if b > 170 and b > r + 60 and g > 90 and g < b + 30 and r < 130:
            pts.append((x, y))
print('crystal px:', len(pts))
# cluster by simple grid bucketing
from collections import deque
seen = set()
clusters = []
ptset = set(pts)
for p in pts:
    if p in seen: continue
    q = deque([p]); seen.add(p); comp = []
    while q:
        cx, cy = q.popleft(); comp.append((cx, cy))
        for dx in (-3, 0, 3):
            for dy in (-3, 0, 3):
                np_ = (cx+dx, cy+dy)
                if np_ in ptset and np_ not in seen:
                    seen.add(np_); q.append(np_)
    if len(comp) > 200:
        xs = [c[0] for c in comp]; ys = [c[1] for c in comp]
        clusters.append((min(xs), max(xs), min(ys), max(ys), len(comp)))
for c in sorted(clusters, key=lambda c: -c[4]):
    print('cluster bbox x %d-%d y %d-%d n=%d center (%.0f, %.0f)' %
          (c[0], c[1], c[2], c[3], c[4], (c[0]+c[1])/2, (c[2]+c[3])/2))

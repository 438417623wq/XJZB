from PIL import Image
from collections import deque

im = Image.open(r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\ceb98bc41cacc4d5590282f1cebdd421.jpg').convert('RGB')
px = im.load()
pts = []
for y in range(300, 1200):
    for x in range(600, 1900):
        r, g, b = px[x, y]
        if b > 170 and b > r + 60 and 90 < g < 230 and r < 130:
            pts.append((x, y))
ptset = set(pts)
seen = set()
clusters = []
for p in pts:
    if p in seen: continue
    q = deque([p]); seen.add(p); comp = []
    while q:
        cx, cy = q.popleft(); comp.append((cx, cy))
        for dx in range(-6, 7, 3):
            for dy in range(-6, 7, 3):
                np_ = (cx + dx, cy + dy)
                if np_ in ptset and np_ not in seen:
                    seen.add(np_); q.append(np_)
    if len(comp) > 60:
        xs = [c[0] for c in comp]; ys = [c[1] for c in comp]
        clusters.append(((min(xs)+max(xs))/2, (min(ys)+max(ys))/2, len(comp), max(xs)-min(xs), max(ys)-min(ys)))
for c in sorted(clusters, key=lambda c: -c[2])[:10]:
    print('cluster center (%.0f, %.0f) n=%d w=%d h=%d' % c)

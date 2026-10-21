from PIL import Image
from collections import Counter

def green_rect(path):
    im = Image.open(path).convert('RGB')
    px = im.load()
    greens = []
    for y in range(800, 1200):
        for x in range(0, 400):
            r, g, b = px[x, y]
            if g > 150 and g > r + 50 and g > b + 50:
                greens.append((x, y))
    rows = Counter(p[1] for p in greens)
    cols = Counter(p[0] for p in greens)
    # horizontal edges: rows with many green px
    hrows = sorted([y for y, c in rows.items() if c > 40])
    vcols = sorted([x for x, c in cols.items() if c > 40])
    return hrows, vcols, greens

for tag, path in [('img1', r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\ceb98bc41cacc4d5590282f1cebdd421.jpg'),
                  ('img2', r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\4609c1ca1ddff126642384561962ebd3.jpg')]:
    hrows, vcols, greens = green_rect(path)
    print(tag, 'long green rows:', hrows)
    print(tag, 'long green cols:', vcols)

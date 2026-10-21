from PIL import Image
im = Image.open(r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\ceb98bc41cacc4d5590282f1cebdd421.jpg').convert('RGB')
px = im.load()
W, H = im.size
# sample: what do crystal pixels actually look like? sample around visible crystals
# display (800,640) -> actual (1049, 839); display (1260,820)->actual (1652,1075)
for (x0, y0, tag) in [(1000, 800, 'crystal1'), (1600, 1050, 'crystal2'), (1300, 300, 'grass')]:
    from collections import Counter
    c = Counter()
    for y in range(y0, y0+60, 3):
        for x in range(x0, x0+60, 3):
            c[px[x, y]] += 1
    print(tag, c.most_common(6))

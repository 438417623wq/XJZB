from PIL import Image
im = Image.open(r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\ceb98bc41cacc4d5590282f1cebdd421.jpg').convert('RGB')
px = im.load()
W,H = im.size
# find greenish pixels anywhere bottom-left quadrant
cnt = {}
greens = []
for y in range(800, 1200):
    for x in range(0, 400):
        r, g, b = px[x, y]
        if g > 150 and g > r + 50 and g > b + 50:
            greens.append((x, y))
print('green px count', len(greens))
if greens:
    xs = [p[0] for p in greens]; ys = [p[1] for p in greens]
    print('green bbox', min(xs), max(xs), min(ys), max(ys))
    # print a few samples
    print(greens[:10])

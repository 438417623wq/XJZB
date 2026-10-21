from PIL import Image
im = Image.open(r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\4609c1ca1ddff126642384561962ebd3.jpg').convert('RGB')
px = im.load()
W, H = im.size
print('img2 flat dark bands (rows with >25% near-black px):')
for y in range(0, H-200, 2):
    cnt = 0
    for x in range(0, W, 8):
        r, g, b = px[x, y]
        if r < 14 and g < 14 and b < 16:
            cnt += 1
    if cnt > (W // 8) * 0.25:
        print('  y=%d frac=%.2f' % (y, cnt / (W // 8)))
print('img2 predicted band rows if world-fixed (world y 400-460):', [round(600+(wy-469)*1.28) for wy in (400, 430, 460)])
# check rows 500-620 specifically for any dark band (with lower threshold)
print('rows 500-620 dark fractions:')
for y in range(500, 620, 4):
    cnt = 0
    for x in range(0, W, 8):
        r, g, b = px[x, y]
        if r < 20 and g < 20 and b < 22:
            cnt += 1
    if cnt > 0:
        print('  y=%d frac=%.2f' % (y, cnt / (W // 8)))

from PIL import Image
im = Image.open(r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\ceb98bc41cacc4d5590282f1cebdd421.jpg').convert('RGB')
px = im.load()
W, H = im.size
Z = 1.2734
CX, CY = 1024.0, None  # camX clamped; camY unknown yet

# per-row dark runs
for y in range(408, 458, 2):
    runs = []
    inrun = False; start = 0
    for x in range(0, W, 4):
        r, g, b = px[x, y]
        dark = r < 14 and g < 14 and b < 16
        if dark and not inrun:
            inrun = True; start = x
        elif not dark and inrun:
            inrun = False
            if x - start > 30: runs.append((start, x))
    if inrun and W - start > 30: runs.append((start, W))
    if runs:
        print('y=%d runs=%s' % (y, runs))

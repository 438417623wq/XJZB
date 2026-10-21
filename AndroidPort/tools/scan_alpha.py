from PIL import Image
import glob, os
base = r'F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide'
for f in sorted(glob.glob(base + r'\c_*.webp')):
    im = Image.open(f)
    print(os.path.basename(f), im.mode, im.size)
    if 'A' not in im.mode:
        continue
    im = im.convert('RGBA')
    W, H = im.size
    px = im.load()
    rows = {}
    total = 0
    for y in range(H):
        for x in range(W):
            if px[x, y][3] < 128:
                total += 1
                rows.setdefault(y, []).append(x)
    if total:
        ys = sorted(rows)
        ranges = []
        s = ys[0]; prev = ys[0]
        for y in ys[1:]:
            if y != prev + 1:
                ranges.append((s, prev)); s = y
            prev = y
        ranges.append((s, prev))
        detail = []
        for (a, b) in ranges[:8]:
            xs = []
            for y in range(a, b + 1):
                xs.extend(rows[y])
            detail.append((a, b, min(xs), max(xs)))
        print('   transparent px:', total, 'ranges(y0,y1,x0,x1):', detail)

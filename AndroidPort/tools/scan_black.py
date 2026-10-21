from PIL import Image
import glob, os
base = r'F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide'
for f in sorted(glob.glob(base + r'\c_*.webp')):
    im = Image.open(f).convert('RGB')
    W, H = im.size
    px = im.load()
    rows = {}
    total_black = 0
    for y in range(H):
        for x in range(W):
            r, g, b = px[x, y]
            if r < 8 and g < 8 and b < 8:
                total_black += 1
                rows.setdefault(y, []).append(x)
    if total_black > 0:
        ys = sorted(rows)
        ranges = []
        s = ys[0]; prev = ys[0]
        for y in ys[1:]:
            if y != prev + 1:
                ranges.append((s, prev)); s = y
            prev = y
        ranges.append((s, prev))
        name = os.path.basename(f)
        # x extent for each range
        detail = []
        for (a, b) in ranges[:6]:
            xs = []
            for y in range(a, b + 1):
                xs.extend(rows[y])
            detail.append((a, b, min(xs), max(xs)))
        print(name, 'size', (W, H), 'blackpx', total_black, 'ranges(y0,y1,x0,x1)', detail)

from PIL import Image
import glob, os

base = r'F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide'
for f in sorted(glob.glob(base + r'\c_*.webp')):
    im = Image.open(f).convert('RGB')
    W, H = im.size
    px = im.load()
    # black mask
    seen = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            r, g, b = px[x, y]
            seen[y][x] = r < 10 and g < 10 and b < 10
    # connected components (4-neigh, iterative)
    comps = []
    for y in range(H):
        for x in range(W):
            if seen[y][x]:
                stack = [(x, y)]
                seen[y][x] = False
                x0 = x1 = x; y0 = y1 = y; n = 0
                while stack:
                    cx, cy = stack.pop()
                    n += 1
                    x0 = min(x0, cx); x1 = max(x1, cx)
                    y0 = min(y0, cy); y1 = max(y1, cy)
                    for nx, ny in ((cx-1,cy),(cx+1,cy),(cx,cy-1),(cx,cy+1)):
                        if 0 <= nx < W and 0 <= ny < H and seen[ny][nx]:
                            seen[ny][nx] = False
                            stack.append((nx, ny))
                if n > 60:  # ignore tiny AA specks
                    comps.append((n, x0, y0, x1, y1))
    if comps:
        name = os.path.basename(f)
        # chunk world offset
        parts = name.replace('c_', '').replace('.webp', '').split('_')
        ox, oy = int(parts[0]) * 512, int(parts[1]) * 512
        for (n, x0, y0, x1, y1) in sorted(comps, reverse=True)[:6]:
            print(f'{name}: black comp {x1-x0+1}x{y1-y0+1}px ({n}px) chunk-local ({x0},{y0})-({x1},{y1}) -> world ({ox+x0},{oy+y0})-({ox+x1},{oy+y1}) tileCol {round((ox+x0)/32,1)}-{round((ox+x1)/32,1)} tileRow {round((oy+y0)/32,1)}-{round((oy+y1)/32,1)}')

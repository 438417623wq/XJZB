from PIL import Image
import glob, os, statistics

base = r'F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide'
for f in sorted(glob.glob(base + r'\c_*.webp')):
    im = Image.open(f).convert('RGB')
    W, H = im.size
    px = im.load()
    parts = os.path.basename(f).replace('c_', '').replace('.webp', '').split('_')
    ox, oy = int(parts[0]) * 512, int(parts[1]) * 512
    hits = []
    for ty in range(0, H, 16):          # 16px = half-tile blocks
        for tx in range(0, W, 16):
            s = 0; n = 0
            for y in range(ty, min(ty+16, H), 2):
                for x in range(tx, min(tx+16, W), 2):
                    r, g, b = px[x, y]
                    s += r + g + b; n += 1
            mean = s / n / 3.0
            if mean < 22:
                hits.append((tx, ty, round(mean, 1)))
    if hits:
        print(os.path.basename(f), 'dark half-tile blocks (local x,y,mean):')
        for h in hits[:20]:
            print('   local(%d,%d) mean=%s -> world(%d,%d) tile(%.1f,%.1f)' %
                  (h[0], h[1], h[2], ox+h[0], oy+h[1], (ox+h[0])/32, (oy+h[1])/32))
        if len(hits) > 20: print('   ...', len(hits), 'total')

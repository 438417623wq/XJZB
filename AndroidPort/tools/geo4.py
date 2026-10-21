from PIL import Image
from collections import Counter

MM_ASSET = 2048.0  # world px (64 tiles * 32)

def calibrate(path, tag):
    im = Image.open(path).convert('RGB')
    W, H = im.size
    px = im.load()
    # clock chip: find PANEL_MID-ish slate rows at screen center x
    # panel mid = rgb(46,54,76); bevel top row PANEL_LITE(88,100,128), bottom PANEL_DARK
    def slate(p):
        r, g, b = p
        return 30 <= r <= 105 and 38 <= g <= 115 and 50 <= b <= 145 and b > r + 8 and b > g + 4
    xs_probe = range(W//2 - 60, W//2 + 60, 12)
    ys = []
    for y in range(0, 120):
        hit = sum(1 for x in xs_probe if slate(px[x, y]))
        if hit > 6:
            ys.append(y)
    chip_top, chip_bot = min(ys), max(ys)
    chipH = chip_bot - chip_top + 1
    dp = chipH / 26.0
    return W, H, px, dp, chipH, (chip_top, chip_bot)

def solve(tag, path, grect):
    W, H, px, dp, chipH, chiptb = calibrate(path, tag)
    mmL = 11 * dp
    mmT = H - (11 + 150) * dp
    mmW = 150 * dp
    gx0, gy0, gx1, gy1 = grect
    gw = gx1 - gx0
    gh = gy1 - gy0
    zoom = W / (gw / mmW * MM_ASSET)
    camX = ((gx0 + gx1) / 2 - mmL) / mmW * MM_ASSET
    camY = ((gy0 + gy1) / 2 - mmT) / mmW * MM_ASSET
    print(f'--- {tag}: {W}x{H} dp={dp:.3f} chipH={chipH} rows={chiptb}')
    print(f'  mmRect inner: L={mmL:.1f} T={mmT:.1f} W={mmW:.1f}')
    print(f'  green rect {gw}x{gh}px -> zoom={zoom:.4f} camX={camX:.1f} camY={camY:.1f}')
    print(f'  tile={32*zoom:.2f}px halfTile={16*zoom:.2f}px chunk={512*zoom:.1f}px')
    print(f'  visible world: {W/zoom:.0f} x {H/zoom:.0f} (map {MM_ASSET:.0f})')
    return W, H, zoom, camX, camY

# img2 green rect measured: (21.5, 877.5)-(315.5, 1013.5)
r2 = solve('img2', r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\4609c1ca1ddff126642384561962ebd3.jpg',
           (21.5, 877.5, 315.5, 1013.5))
# img1: detect with lower threshold
im1 = Image.open(r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\ceb98bc41cacc4d5590282f1cebdd421.jpg').convert('RGB')
p1 = im1.load()
greens = []
for y in range(800, 1200):
    for x in range(0, 400):
        r, g, b = p1[x, y]
        if g > 140 and g > r + 40 and g > b + 40:
            greens.append((x, y))
rows = Counter(p[1] for p in greens); cols = Counter(p[0] for p in greens)
hrows = sorted([y for y, c in rows.items() if c > 25])
vcols = sorted([x for x, c in cols.items() if c > 25])
print('img1 long green rows:', hrows, 'cols:', vcols)
if hrows and vcols:
    r1 = solve('img1', r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\ceb98bc41cacc4d5590282f1cebdd421.jpg',
               (vcols[0], hrows[0], vcols[-1], hrows[-1]))

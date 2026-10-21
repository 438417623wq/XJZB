from PIL import Image
import statistics

def analyze(path, tag):
    im = Image.open(path).convert('RGB')
    W, H = im.size
    px = im.load()

    # --- 1. find green viewport rect on minimap (bright green stroke) ---
    greens = []
    for y in range(850, 1200):
        for x in range(0, 360):
            r, g, b = px[x, y]
            if g > 200 and r < 130 and b < 130:
                greens.append((x, y))
    gx0 = min(p[0] for p in greens); gx1 = max(p[0] for p in greens)
    gy0 = min(p[1] for p in greens); gy1 = max(p[1] for p in greens)
    # stroke adds ~1px each side; rect interior
    gw = gx1 - gx0; gh = gy1 - gy0

    # --- 2. calibrate dp from RES chip: find its left/right edges via bevel panel color ---
    # instead: use clock chip (64dp wide). find the dark bevel chip rows at top center.
    # scan row y=40 for the chip: chip is dark slate (PANEL_MID) vs terrain
    # measure bevel panel color from pause chip area first
    # simpler: locate clock chip by the "00:26" white text cluster at top center
    whites = []
    for y in range(10, 80):
        for x in range(W//2 - 150, W//2 + 150):
            r, g, b = px[x, y]
            if r > 215 and g > 215 and b > 215:
                whites.append((x, y))
    cx = (min(p[0] for p in whites) + max(p[0] for p in whites)) / 2
    # chip is centered at W/2; chip width = 64dp -> dp = measured chip? we know text ~ centered
    # calibrate dp from res chip: res chip left edge = pause.right+10dp, but text width unknown.
    # use clock text center to confirm W/2 anchoring, and calibrate dp from CHIP height:
    # find chip vertical extent at x=W/2: bevel slate color rows
    def slate(p):
        r,g,b = p
        return 28 <= r <= 66 and 34 <= g <= 72 and 44 <= b <= 90 and b >= r
    ys_chip = [y for y in range(0, 110) if slate(px[int(cx), y])]
    chipH_px = max(ys_chip) - min(ys_chip) + 1 if ys_chip else 0
    dp = chipH_px / 26.0

    mmW = (150 + 6 - 6) * dp          # minimap inner width = 150dp (slot 156dp minus 2*3dp)
    mmL = (8 + 3) * dp                 # minimap inner left
    mmT = H - (8 + 3) * dp - 150 * dp  # minimap inner top

    # --- 3. solve zoom & camera ---
    wPx = 64 * 32
    zoom = W / (gw / mmW * wPx)
    camX = ((gx0 + gx1) / 2 - mmL) / mmW * wPx
    camY = ((gy0 + gy1) / 2 - mmT) / mmW * wPx
    print(f'--- {tag}: size {W}x{H}')
    print(f'  green rect px: ({gx0},{gy0})-({gx1},{gy1})  {gw}x{gh}')
    print(f'  dp={dp:.3f} chipH={chipH_px} mmRect inner=({mmL:.1f},{mmT:.1f})+{mmW:.1f}')
    print(f'  zoom={zoom:.4f}  camX={camX:.1f} camY={camY:.1f}')
    print(f'  tile on screen = {32*zoom:.1f}px, chunk on screen = {512*zoom:.1f}px')
    return px, W, H, zoom, camX, camY, mmL, mmT, mmW

def to_world(px, W, H, zoom, camX, camY, sx, sy):
    return camX + (sx - W/2)/zoom, camY + (sy - H/2)/zoom

# image 1
px1, W1, H1, z1, cx1, cy1, ml1, mt1, mw1 = analyze(
    r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\ceb98bc41cacc4d5590282f1cebdd421.jpg', 'img1 00:26')

# strip1 world y
for (label, sy) in [('strip1-left y414-432', 423), ('strip1-right y436-450', 443),
                    ('strip2-dim y1102-1116', 1109), ('strip2-dark y1118-1137', 1127)]:
    wy = cy1 + (sy - H1/2)/z1
    print(f'  {label}: worldY={wy:.1f}  tileRow={wy/32:.2f}  chunkRow={wy/512:.3f}')
# blob world
bwx = cx1 + (2450 - W1/2)/z1; bwy = cy1 + (721 - H1/2)/z1
print(f'  blob(2450,721): world=({bwx:.1f},{bwy:.1f}) tile=({bwx/32:.2f},{bwy/32:.2f})')

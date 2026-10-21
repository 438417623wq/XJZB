from PIL import Image
import statistics

for tag, path in [('img1', r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\ceb98bc41cacc4d5590282f1cebdd421.jpg'),
                  ('img2', r'H:\weixin\xwechat_files\wxid_5qjiqibd0r0q22_8156\temp\RWTemp\2026-10\4609c1ca1ddff126642384561962ebd3.jpg')]:
    im = Image.open(path).convert('RGB')
    W, H = im.size
    px = im.load()
    # find the black minimap interior: large near-black region in bottom-left
    xs, ys = [], []
    for y in range(850, 1200):
        for x in range(0, 400):
            r, g, b = px[x, y]
            if r < 25 and g < 25 and b < 25:
                xs.append(x); ys.append(y)
    # the minimap interior is textured though; use the bevel frame instead:
    # scan row y=1150 (inside slot) for the slot's dark frame boundaries
    # simpler: the minimap is drawn OVER black bg; interior mostly non-black.
    # Use: leftmost/rightmost extent of the bevel PANEL_MID color at row H-30
    def midc(p):
        r, g, b = p
        return 30 <= r <= 60 and 38 <= g <= 70 and 55 <= b <= 95
    y_probe = H - 20
    runs = [x for x in range(0, 420) if midc(px[x, y_probe])]
    if runs:
        print(tag, 'bevel frame cols at y=H-20:', runs[:8], '...', runs[-8:] if len(runs) > 8 else '')
    # black interior bbox (minimap rect itself):
    print(tag, 'nearblack bbox x', min(xs), max(xs), 'y', min(ys), max(ys))

    # right-edge beyond-map check: sample columns near W
    for xx in (W-260, W-200, W-120, W-60, W-8):
        col = [px[xx, y] for y in range(200, 1000, 25)]
        mean = tuple(round(statistics.mean(v[i] for v in col), 1) for i in range(3))
        var = round(statistics.pstdev([v[0]+v[1]+v[2] for v in col]), 1)
        print(tag, f'col x={xx}: mean={mean} rgbsum-stdev={var}')

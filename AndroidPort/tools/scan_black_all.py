from PIL import Image
import glob, os
base = r'F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps'
hits = []
for dp, _dn, fn in os.walk(base):
    for f in fn:
        if not f.endswith('.webp'):
            continue
        p = os.path.join(dp, f)
        im = Image.open(p).convert('RGB')
        W, H = im.size
        px = im.load()
        seen = bytearray(W * H)
        black = bytearray(W * H)
        for y in range(H):
            off = y * W
            for x in range(W):
                r, g, b = px[x, y]
                black[off + x] = 1 if (r < 8 and g < 8 and b < 8) else 0
        for i0 in range(W * H):
            if not black[i0] or seen[i0]:
                continue
            stack = [i0]
            seen[i0] = 1
            n = 0
            x0 = x1 = i0 % W
            y0 = y1 = i0 // W
            while stack:
                i = stack.pop()
                n += 1
                x = i % W; y = i // W
                if x < x0: x0 = x
                if x > x1: x1 = x
                if y < y0: y0 = y
                if y > y1: y1 = y
                for j in (i - 1 if x > 0 else -1, i + 1 if x < W - 1 else -1,
                          i - W if y > 0 else -1, i + W if y < H - 1 else -1):
                    if j >= 0 and black[j] and not seen[j]:
                        seen[j] = 1
                        stack.append(j)
            if x1 - x0 + 1 >= 8 and y1 - y0 + 1 >= 8:
                rel = os.path.relpath(p, base)
                hits.append((rel, x1 - x0 + 1, y1 - y0 + 1, n, x0, y0))
print('files with >=8x8 pure-black components:', len(hits))
for h in hits[:40]:
    print('  %s: %dx%d bbox (%d,%d) n=%d' % h)

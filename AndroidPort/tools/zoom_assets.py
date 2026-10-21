from PIL import Image
base = r'F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide'
mm = Image.open(base + r'\minimap.webp').convert('RGB')
print('minimap region (200-256, 50-110) enlarged 8x:')
mm.crop((200, 50, 256, 110)).resize((448, 480), Image.NEAREST).save(
    r'F:\KF\XJZB\AndroidPort\tools\_mm_blob.png')
ck = Image.open(base + r'\c_3_1.webp').convert('RGB')
print('chunk c_3_1 region (380-512, 120-230) enlarged 3x:')
ck.crop((380, 120, 512, 230)).resize((396, 330), Image.NEAREST).save(
    r'F:\KF\XJZB\AndroidPort\tools\_ck_blob.png')
# also check the tile-pixel stats of the blob area in the chunk
px = ck.load()
from collections import Counter
c = Counter()
for y in range(150, 200):
    for x in range(430, 512):
        c[px[x, y]] += 1
print('chunk blob-area top colors:', c.most_common(6))
mmpx = mm.load()
c2 = Counter()
for y in range(75, 95):
    for x in range(230, 256):
        c2[mmpx[x, y]] += 1
print('minimap blob-area top colors:', c2.most_common(6))

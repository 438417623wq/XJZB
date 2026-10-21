from PIL import Image
base = r'F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\divide'
out = Image.new('RGB', (4 * 512, 100), (255, 0, 255))
for i, cx in enumerate(range(4)):
    im = Image.open(base + ('\c_%d_0.webp' % cx)).convert('RGB')
    out.paste(im.crop((0, 360, 512, 460)), (i * 512, 0))
out.save(r'F:\KF\XJZB\AndroidPort\tools\_striprow.png')
print('saved: 4 chunks c_x_0, local y 360-460 (100px tall), left->right = chunk col 0..3')

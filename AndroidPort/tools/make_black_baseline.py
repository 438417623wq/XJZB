"""v2.42: black-pixel baseline per terrain chunk, read from the shipped v2.41 APK.

The re-bake only ever REMOVES pure-black terrain, so this table is a floor: the
[v242] asset assertion fails if any chunk carries more black than it did in
v2.41. numpy keeps the 5012-chunk sweep to seconds.
"""
import io, sys, zipfile
import numpy as np
from PIL import Image

APK = sys.argv[1] if len(sys.argv) > 1 else \
    r'F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk'
OUT = r'F:\KF\XJZB\AndroidPort\tools\black_baseline.txt'

z = zipfile.ZipFile(APK)
rows = []
for n in z.namelist():
    if not (n.startswith('assets/maps/') and '/c_' in n and n.endswith('.webp')):
        continue
    parts = n.split('/')
    mid, fn = parts[-2], parts[-1]
    im = Image.open(io.BytesIO(z.read(n))).convert('RGB')
    a = np.asarray(im, dtype=np.uint8)
    cnt = int(np.count_nonzero(np.all(a < 8, axis=2)))
    rows.append('%s/%s %d' % (mid, fn, cnt))
with open(OUT, 'w', encoding='utf8') as fp:
    fp.write('\n'.join(rows) + '\n')
print('baseline rows:', len(rows))

import zipfile, os
z = zipfile.ZipFile(r'F:\KF\XJZB\AndroidPort\星际争霸RTS-v2.41.apk')
old = {}
for n in z.namelist():
    if n.startswith('assets/maps/') and n.endswith('.webp'):
        old[n] = z.getinfo(n).file_size
base = r'F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps'
new = {}
for dp, _dn, fn in os.walk(base):
    for f in fn:
        if f.endswith('.webp'):
            p = os.path.join(dp, f)
            rel = 'assets/maps/' + os.path.relpath(p, base).replace(os.sep, '/')
            new[rel] = os.path.getsize(p)
print('old webp count', len(old), 'sum MB', round(sum(old.values())/1e6, 1))
print('new webp count', len(new), 'sum MB', round(sum(new.values())/1e6, 1))
for mid in ('losttemple', 'frozensea', 'divide', 'acropolis'):
    o = sum(v for k, v in old.items() if k.startswith('assets/maps/%s/' % mid))
    n = sum(v for k, v in new.items() if k.startswith('assets/maps/%s/' % mid))
    oc = sum(1 for k in old if k.startswith('assets/maps/%s/' % mid) and '/c_' in k)
    nc = sum(1 for k in new if k.startswith('assets/maps/%s/' % mid) and '/c_' in k)
    print('%s: old %d chunks %.1fMB | new %d chunks %.1fMB' % (mid, oc, o/1e6, nc, n/1e6))
import io
from PIL import Image
o1 = Image.open(io.BytesIO(z.read('assets/maps/losttemple/c_0_0.webp')))
n1 = Image.open(base + os.sep + 'losttemple' + os.sep + 'c_0_0.webp')
print('losttemple c_0_0: old', o1.size, o1.mode, 'new', n1.size, n1.mode)

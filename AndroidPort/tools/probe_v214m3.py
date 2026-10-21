from PIL import Image
import os
SPR = r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\sprites"
tot = {3:0, 6:0}
n = 0
worst = []
for f in sorted(os.listdir(SPR)):
    if not f.endswith(".webp"): continue
    p = os.path.join(SPR, f)
    cur = os.path.getsize(p)
    im = Image.open(p)
    if im.mode not in ("RGBA","RGB"): im = im.convert("RGBA")
    s6 = cur
    import io
    b = io.BytesIO(); im.save(b, "WEBP", lossless=True, method=3); s3 = b.tell()
    tot[3] += s3; tot[6] += s6; n += 1
    if s3 > s6: worst.append((s3-s6, f, s6, s3))
worst.sort(reverse=True)
print("files=%d  method3 total=%.1f KB  method6 total=%.1f KB  delta=%+.1f KB (%.2f%%)"
      % (n, tot[3]/1024, tot[6]/1024, (tot[3]-tot[6])/1024, 100.0*(tot[3]-tot[6])/tot[6]))
print("largest regressions:")
for d,f,a,b2 in worst[:8]: print("   +%5d B  %-24s %d -> %d" % (d,f,a,b2))

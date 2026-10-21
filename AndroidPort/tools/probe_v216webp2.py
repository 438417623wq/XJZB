import os, io
from PIL import Image, ImageChops
import numpy as np
base=r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\hunters"
files=sorted(f for f in os.listdir(base) if f.startswith("c_") and f.endswith(".webp"))
ims=[Image.open(os.path.join(base,f)).convert("RGB") for f in files]
tot_l=sum(os.path.getsize(os.path.join(base,f)) for f in files)
print("lossless total=%d" % tot_l)
for q in (80,85,90,95,100):
    for m in (4,6):
        tot=0; mx=0
        for im in ims:
            b=io.BytesIO(); im.save(b,"WEBP",lossless=False,quality=q,method=m)
            tot+=len(b.getvalue())
            d=np.asarray(ImageChops.difference(im,Image.open(io.BytesIO(b.getvalue())).convert("RGB")),dtype=np.int32)
            mx=max(mx,int(d.max()))
        print("q%-3d m%d total=%8d ratio=%.2fx maxdiff=%3d" % (q,m,tot,tot_l/tot,mx))

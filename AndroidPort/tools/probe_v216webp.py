import os, io
from PIL import Image, ImageChops
import numpy as np
base=r"F:\KF\XJZB\AndroidPort\app\app\src\main\assets\maps\hunters"
files=sorted(f for f in os.listdir(base) if f.startswith("c_") and f.endswith(".webp"))
tot_l=tot_q=0
worst=0; worstf=""
for f in files:
    p=os.path.join(base,f)
    im=Image.open(p).convert("RGB")
    tot_l+=os.path.getsize(p)
    b=io.BytesIO(); im.save(b,"WEBP",lossless=False,quality=80,method=4)
    tot_q+=len(b.getvalue())
    q=Image.open(io.BytesIO(b.getvalue())).convert("RGB")
    d=np.asarray(ImageChops.difference(im,q),dtype=np.int32)
    mx=int(d.max()); mean=float(d.mean())
    if mx>worst: worst=mx; worstf=f
    print("%-14s lossless=%8d q80=%8d  maxdiff=%3d meandiff=%.2f" % (f,os.path.getsize(p),len(b.getvalue()),mx,mean))
print("TOTAL lossless=%d q80=%d ratio=%.2fx  worst maxdiff=%d (%s)" % (
    tot_l,tot_q,tot_l/tot_q,worst,worstf))

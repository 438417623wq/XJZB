import os, sys
import numpy as np
sys.path.insert(0,'.')
import pipeline_maps as pm
for n in [r"maps\ladder\(4)Dire Straits.scm", r"maps\ladder\(4)Lost Temple.scm"]:
    r=pm.read_chk(os.path.join(pm.ROOT,n)); chk,gaps=r; g,sec=pm.parse_chk(chk,gaps)
    off,_=sec[b"DIM "]; w,h=g.u16(off),g.u16(off+2)
    mo,_=sec[b"MTXM"]; mt=[g.u16(mo+i*2) for i in range(w*h)]
    ts=pm.load_tileset("jungle")
    walk=pm._walk_bitmap(w,h,mt,ts)
    print("===", os.path.basename(n), w,h)
    # downsample to w cols by sampling center of each 32x32 tile (8 minitiles)
    for ty in range(h):
        row=[]
        for tx in range(w):
            blk=walk[ty*4:(ty+1)*4, tx*4:(tx+1)*4]
            row.append("#" if blk.mean()>0.5 else ("+" if blk.any() else "."))
        print("".join(row))

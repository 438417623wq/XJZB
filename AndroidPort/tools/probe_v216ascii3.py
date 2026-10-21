import os, sys
sys.path.insert(0,'.')
import numpy as np
import pipeline_maps as pm
from collections import deque

def walk_any(w,h,mtwm,ts):
    m=np.asarray(mtwm,dtype=np.uint32).reshape(h,w)
    grp=np.clip((m&0x7FF0)>>4,0,len(ts["cv5_tiles"])-1); var=m&0xF
    tiles=np.asarray(ts["cv5_tiles"],dtype=np.int64)
    vx4m=np.clip(tiles[grp,var],0,len(ts["vf4_flags"])-1)
    f=np.asarray(ts["vf4_flags"],dtype=np.int64)[vx4m].reshape(h,w,4,4)
    return (f!=0).astype(np.uint8).transpose(0,2,1,3).reshape(h*4,w*4)

def load(n):
    r=pm.read_chk(os.path.join(pm.ROOT,n)); chk,gaps=r; g,sec=pm.parse_chk(chk,gaps)
    off,_=sec[b"DIM "]; w,h=g.u16(off),g.u16(off+2)
    mo,_=sec[b"MTXM"]; mt=[g.u16(mo+i*2) for i in range(w*h)]
    eo,_=sec[b"ERA "]; ts=pm.load_tileset(pm.TILESETS[g.byte(eo)])
    return w,h,walk_any(w,h,mt,ts), pm._starts_of(g,sec)

for name,path in [('DireStraits',r"maps\ladder\(4)Dire Straits.scm"),
                  ('Hypothermia',r"maps\BroodWar\(6)Hypothermia.scx")]:
    w,h,walk,starts=load(path)
    W,H=w*4,h*4
    print("===",name,w,h,"starts",starts)
    step=4
    for y in range(0,H,step*4):
        row=[]
        for x in range(0,W,step*4):
            blk=walk[y:y+step*4, x:x+step*4]
            row.append("#" if blk.mean()>0.4 else ("+" if blk.any() else "."))
        marks=list("".join(row))
        for sx,sy in starts:
            if abs(sy-y)<step*4:
                ci=sx//(step*4)
                if 0<=ci<len(marks): marks[ci]="S"
        print("".join(marks))

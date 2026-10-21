import os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_maps as pm
from gapio import GapReader

def walk_of(src):
    r = pm.read_chk(os.path.join(pm.ROOT, src))
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    off,_ = sec[b"DIM "]; w,h = g.u16(off), g.u16(off+2)
    eoff,_ = sec[b"ERA "]; ts = pm.load_tileset(pm.TILESETS[g.byte(eoff)])
    off,size = sec[b"MTXM"]
    mtwm=[g.u16(off+i*2) for i in range(w*h)]
    walk=bytearray(w*4*h*4); starts=[]
    for ty in range(h):
        for tx in range(w):
            raw=mtwm[ty*w+tx]; grp=(raw&0x7FF0)>>4; var=raw&0xF
            if grp>=len(ts["cv5_tiles"]): grp=0
            vx4m=ts["cv5_tiles"][grp][var]
            if vx4m>=len(ts["vx4_refs"]): vx4m=0
            flags=ts["vf4_flags"][vx4m] if vx4m<len(ts["vf4_flags"]) else None
            for k in range(16):
                wk=1 if (flags is not None and (flags[k]&1)) else 0
                walk[(ty*4+(k//4))*(w*4)+(tx*4+(k%4))]=wk
    uo,us=sec[b"UNIT"]
    for i in range(us//36):
        b=uo+i*36
        if g.u16(b+8)==pm.START_ID: starts.append((g.u16(b+4)//8, g.u16(b+6)//8))
    return w,h,walk,starts

for name in [r"maps\scenario\(4)King of the Hill.scm", r"maps\ladder\(4)Dire Straits.scm", r"maps\(2)The Small Divide.scm"]:
    w,h,walk,starts=walk_of(name)
    W,H=w*4,h*4
    im=Image.new("RGB",(W,H)); px=im.load()
    for y in range(H):
        for x in range(W): px[x,y]=(210,210,210) if walk[y*W+x] else (30,8,8)
    for sx,sy in starts:
        for dx in range(-5,6):
            for dy in range(-5,6):
                xx,yy=sx+dx,sy+dy
                if 0<=xx<W and 0<=yy<H: px[xx,yy]=(0,255,0)
    out=os.path.basename(name).replace(".scm","")+"_walk.png"
    im.save(out); print("saved",out,w,h,"starts",starts,"walk",sum(walk),"/",W*H)

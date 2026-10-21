import os, sys
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_maps as pm

def raw_tiles(src):
    r = pm.read_chk(os.path.join(pm.ROOT, src))
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    off,_ = sec[b"DIM "]; w,h = g.u16(off), g.u16(off+2)
    eoff,_ = sec[b"ERA "]; ts = pm.load_tileset(pm.TILESETS[g.byte(eoff)])
    off,size = sec[b"MTXM"]
    mtwm=[g.u16(off+i*2) for i in range(w*h)]
    starts=[]
    uo,us=sec[b"UNIT"]
    for i in range(us//36):
        b=uo+i*36
        if g.u16(b+8)==pm.START_ID: starts.append((g.u16(b+4)//8, g.u16(b+6)//8))
    return w,h,mtwm,ts,starts

def walk_bit(w,h,mtwm,ts,bit):
    walk=bytearray(w*4*h*4)
    for ty in range(h):
        for tx in range(w):
            raw=mtwm[ty*w+tx]; grp=(raw&0x7FF0)>>4; var=raw&0xF
            if grp>=len(ts["cv5_tiles"]): grp=0
            vx4m=ts["cv5_tiles"][grp][var]
            if vx4m>=len(ts["vx4_refs"]): vx4m=0
            flags=ts["vf4_flags"][vx4m] if vx4m<len(ts["vf4_flags"]) else None
            for k in range(16):
                wk=1 if (flags is not None and (flags[k]>>bit)&1) else 0
                walk[(ty*4+(k//4))*(w*4)+(tx*4+(k%4))]=wk
    return walk

def comp_stats(walk,W,H):
    lab=[-1]*(W*H); c=0; sizes=[]
    for i in range(W*H):
        if walk[i] and lab[i]<0:
            q=deque([i]); lab[i]=c; n=0
            while q:
                p=q.popleft(); n+=1; x=p%W; y=p//W
                if x>0 and walk[p-1] and lab[p-1]<0: lab[p-1]=c; q.append(p-1)
                if x<W-1 and walk[p+1] and lab[p+1]<0: lab[p+1]=c; q.append(p+1)
                if y>0 and walk[p-W] and lab[p-W]<0: lab[p-W]=c; q.append(p-W)
                if y<H-1 and walk[p+W] and lab[p+W]<0: lab[p+W]=c; q.append(p+W)
            c+=1; sizes.append(n)
    return c, lab, sizes

for name in [r"maps\(2)The Small Divide.scm", r"maps\ladder\(4)Dire Straits.scm"]:
    w,h,mtwm,ts,starts=raw_tiles(name)
    W,H=w*4,h*4
    print("===", os.path.basename(name), w,h)
    for bit in range(16):
        walk=walk_bit(w,h,mtwm,ts,bit)
        n=sum(walk)
        c,lab,sizes=comp_stats(walk,W,H)
        biggest=max(sizes) if sizes else 0
        labs=[lab[(lambda z:z[1]*W+z[0])(pm and 0 or 0)] ] if False else None
        print("  bit%2d walkable=%6d comps=%4d biggest=%6d (%.0f%%)" % (
            bit, n, c, biggest, 100.0*biggest/max(1,W*H)))

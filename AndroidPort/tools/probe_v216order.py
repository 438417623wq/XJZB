import os, sys
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_maps as pm

def raw(src):
    r = pm.read_chk(os.path.join(pm.ROOT, src)); chk,gaps=r
    g,sec=pm.parse_chk(chk,gaps)
    off,_=sec[b"DIM "]; w,h=g.u16(off),g.u16(off+2)
    eoff,_=sec[b"ERA "]; ts=pm.load_tileset(pm.TILESETS[g.byte(eoff)])
    off,size=sec[b"MTXM"]; mtwm=[g.u16(off+i*2) for i in range(w*h)]
    starts=[]
    uo,us=sec[b"UNIT"]
    for i in range(us//36):
        b=uo+i*36
        if g.u16(b+8)==pm.START_ID: starts.append((g.u16(b+4)//8,g.u16(b+6)//8))
    return w,h,mtwm,ts,starts

def walk_order(w,h,mtwm,ts,order):
    walk=bytearray(w*4*h*4)
    for ty in range(h):
        for tx in range(w):
            r0=mtwm[ty*w+tx]; grp=(r0&0x7FF0)>>4; var=r0&0xF
            if grp>=len(ts["cv5_tiles"]): grp=0
            vx4m=ts["cv5_tiles"][grp][var]
            if vx4m>=len(ts["vx4_refs"]): vx4m=0
            flags=ts["vf4_flags"][vx4m] if vx4m<len(ts["vf4_flags"]) else None
            for k in range(16):
                fk = k if order=="row" else (k%4)*4+(k//4)
                wk=1 if (flags is not None and (flags[fk]&1)) else 0
                walk[(ty*4+(k//4))*(w*4)+(tx*4+(k%4))]=wk
    return walk

def stats(walk,W,H,starts):
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
    def near(x,y):
        for rr in range(0,16):
            for dx in range(-rr,rr+1):
                for dy in range(-rr,rr+1):
                    xx,yy=x+dx,y+dy
                    if 0<=xx<W and 0<=yy<H and walk[yy*W+xx]: return lab[yy*W+xx]
        return None
    labs=[near(x,y) for x,y in starts]
    return c, max(sizes) if sizes else 0, labs, sum(walk)

for name in [r"maps\ladder\(4)Dire Straits.scm", r"maps\(2)The Small Divide.scm",
             r"maps\ladder\(4)Lost Temple.scm", r"maps\(4)Blood Bath.scm",
             r"maps\BroodWar\(4)River Lethe.scx", r"maps\BroodWar\(8)Primeval Isles.scx"]:
    w,h,mtwm,ts,starts=raw(name); W,H=w*4,h*4
    print("===", os.path.basename(name), w,h, "starts", starts)
    for order in ("row","col"):
        walk=walk_order(w,h,mtwm,ts,order)
        c,big,labs,wk=stats(walk,W,H,starts)
        print("  %s comps=%3d biggest=%6d walk=%6d labs=%s conn=%s" % (
            order,c,big,wk,labs,len(set(labs))==1))

import os, sys, json
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_maps as pm

def build_walk(src):
    r = pm.read_chk(os.path.join(pm.ROOT, src))
    if not r: return None
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    if b"DIM " not in sec or b"MTXM" not in sec or b"ERA " not in sec: return None
    off,_ = sec[b"DIM "]; w,h = g.u16(off), g.u16(off+2)
    if w>256 or h>256 or w<32 or h<32: return None
    eoff,_ = sec[b"ERA "]; ts = pm.load_tileset(pm.TILESETS.get(g.byte(eoff), "platform"))
    if ts is None: return None
    off,size = sec[b"MTXM"]
    mtwm = [g.u16(off+i*2) for i in range(w*h)]
    walk = bytearray(w*4*h*4)
    for ty in range(h):
        for tx in range(w):
            raw = mtwm[ty*w+tx]
            grp=(raw & 0x7FF0)>>4; var=raw & 0xF
            if grp>=len(ts["cv5_tiles"]): grp=0
            vx4m=ts["cv5_tiles"][grp][var]
            if vx4m>=len(ts["vx4_refs"]): vx4m=0
            flags=ts["vf4_flags"][vx4m] if vx4m<len(ts["vf4_flags"]) else None
            for k in range(16):
                wk = 1 if (flags is not None and (flags[k] & 1)) else 0
                X4=tx*4+(k%4); Y4=ty*4+(k//4)
                walk[Y4*(w*4)+X4]=wk
    starts=[]; mins=0; geys=0
    if b"UNIT" in sec:
        uo,us = sec[b"UNIT"]
        for i in range(us//36):
            base=uo+i*36; uid=g.u16(base+8); x=g.u16(base+4); y=g.u16(base+6)
            if uid in pm.MINERAL_IDS: mins+=1
            elif uid==pm.GEYSER_ID: geys+=1
            elif uid==pm.START_ID: starts.append((x,y))
    return w,h,walk,starts,mins,geys

def label(walk,W,H):
    lab=[-1]*(W*H); comp=0
    for i in range(W*H):
        if walk[i] and lab[i]<0:
            q=deque([i]); lab[i]=comp
            while q:
                p=q.popleft(); x=p%W; y=p//W
                if x>0 and walk[p-1] and lab[p-1]<0: lab[p-1]=comp; q.append(p-1)
                if x<W-1 and walk[p+1] and lab[p+1]<0: lab[p+1]=comp; q.append(p+1)
                if y>0 and walk[p-W] and lab[p-W]<0: lab[p-W]=comp; q.append(p-W)
                if y<H-1 and walk[p+W] and lab[p+W]<0: lab[p+W]=comp; q.append(p+W)
            comp+=1
    return lab,comp

def near(walk,W,H,x,y):
    for r in range(0,16):
        for dx in range(-r,r+1):
            for dy in range(-r,r+1):
                xx,yy=x+dx,y+dy
                if 0<=xx<W and 0<=yy<H and walk[yy*W+xx]: return xx,yy
    return None

def check(src):
    res=build_walk(src)
    if res is None: return None
    w,h,walk,starts,mins,geys=res
    W,H=w*4,h*4
    lab,comp=label(walk,W,H)
    labs=[]
    for px,py in starts:
        n=near(walk,W,H,px//8,py//8)
        labs.append(None if n is None else lab[n[1]*W+n[0]])
    ok = len(starts)>=2 and all(l is not None for l in labs) and len(set(labs))==1
    return dict(w=w,h=h,starts=len(starts),mins=mins,geys=geys,ok=ok,
                comps=comp,startlabs=labs,walkable=sum(1 for v in walk if v))

files=[]
for dp,dn,fn in os.walk(r"F:\KF\XJZB\maps"):
    for f in fn:
        if f.lower().endswith((".scm",".scx")): files.append(os.path.join(dp,f))
files.sort()
print("total:",len(files))
results={}
for f in files:
    rel=os.path.relpath(f, pm.ROOT)
    try: r=check(rel)
    except Exception as e: print("ERR",os.path.basename(f),e); continue
    results[os.path.basename(f)]=r
    if r is None: print("%-46s NOBUILD" % os.path.basename(f)); continue
    print("%-44s %3dx%-3d st=%d m=%3d g=%2d conn=%-5s comps=%d" % (
        os.path.basename(f), r["w"],r["h"],r["starts"],r["mins"],r["geys"],r["ok"],r["comps"]))
json.dump(results, open("_v216conn.json","w"), ensure_ascii=False)
print("saved")

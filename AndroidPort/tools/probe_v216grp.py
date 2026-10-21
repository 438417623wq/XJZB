import os, sys, json
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_v216bits as pb

def walk_grp(w,h,mtwm,ts):
    walk=bytearray(w*4*h*4)
    for ty in range(h):
        for tx in range(w):
            r0=mtwm[ty*w+tx]; grp=(r0&0x7FF0)>>4
            if grp>=len(ts["cv5_tiles"]): grp=0
            flags=ts["vf4_flags"][grp] if grp<len(ts["vf4_flags"]) else None
            for k in range(16):
                wk=1 if (flags is not None and (flags[k]&1)) else 0
                walk[(ty*4+(k//4))*(w*4)+(tx*4+(k%4))]=wk
    return walk

def check(walk,W,H,starts):
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
        for rr in range(0,24):
            for dx in range(-rr,rr+1):
                for dy in range(-rr,rr+1):
                    xx,yy=x+dx,y+dy
                    if 0<=xx<W and 0<=yy<H and walk[yy*W+xx]: return lab[yy*W+xx]
        return None
    labs=[near(x,y) for x,y in starts]
    return labs, (len(starts)>=2 and None not in labs and len(set(labs))==1), c, (max(sizes) if sizes else 0)

files=[]
for dp,dn,fn in os.walk(r"F:\KF\XJZB\maps"):
    for f in fn:
        if f.lower().endswith((".scm",".scx")): files.append(os.path.join(dp,f))
files.sort()
res={}
for f in files:
    n=os.path.basename(f)
    try:
        w,h,mtwm,ts,starts=pb.raw(os.path.relpath(f, pb.pm.ROOT))
    except Exception as e:
        res[n]=None; continue
    W,H=w*4,h*4
    labs,ok,c,big=check(walk_grp(w,h,mtwm,ts),W,H,starts)
    res[n]=dict(w=w,h=h,starts=len(starts),ok=ok,comps=c,big=big,labs=labs)
    print("%-44s %3dx%-3d st=%d conn=%-5s comps=%4d big=%3.0f%%" % (
        n,w,h,len(starts),ok,c,100.0*big/(W*H)))
json.dump(res, open("_v216grp.json","w"), ensure_ascii=False)
print("saved")

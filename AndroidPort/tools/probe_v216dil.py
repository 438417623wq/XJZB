import os, sys
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_maps as pm
import probe_v216bits as pb

def dilate(walk,W,H,r):
    out=bytearray(W*H)
    for y in range(H):
        for x in range(W):
            if not walk[y*W+x]: continue
            for dy in range(-r,r+1):
                yy=y+dy
                if yy<0 or yy>=H: continue
                base=yy*W
                for dx in range(-r,r+1):
                    xx=x+dx
                    if 0<=xx<W: out[base+xx]=1
    return out

def conn(walk,W,H,starts):
    lab=[-1]*(W*H); c=0
    for i in range(W*H):
        if walk[i] and lab[i]<0:
            q=deque([i]); lab[i]=c
            while q:
                p=q.popleft(); x=p%W; y=p//W
                if x>0 and walk[p-1] and lab[p-1]<0: lab[p-1]=c; q.append(p-1)
                if x<W-1 and walk[p+1] and lab[p+1]<0: lab[p+1]=c; q.append(p+1)
                if y>0 and walk[p-W] and lab[p-W]<0: lab[p-W]=c; q.append(p-W)
                if y<H-1 and walk[p+W] and lab[p+W]<0: lab[p+W]=c; q.append(p+W)
            c+=1
    def near(x,y):
        for rr in range(0,20):
            for dx in range(-rr,rr+1):
                for dy in range(-rr,rr+1):
                    xx,yy=x+dx,y+dy
                    if 0<=xx<W and 0<=yy<H and walk[yy*W+xx]: return lab[yy*W+xx]
        return None
    labs=[near(x,y) for x,y in starts]
    return labs, len(set(labs))==1

tests=[r"maps\ladder\(4)Dire Straits.scm", r"maps\(2)The Small Divide.scm",
       r"maps\ladder\(6)Polaris Prime.scm", r"maps\ladder\(4)Lost Temple.scm",
       r"maps\(4)Blood Bath.scm", r"maps\BroodWar\(4)River Lethe.scx",
       r"maps\BroodWar\(8)Primeval Isles.scx", r"maps\scenario\(4)King of the Hill.scm",
       r"maps\BroodWar\(6)Sapphire Isles.scx", r"maps\(5)Island Hop.scm"]
cache={n:pb.raw(n) for n in tests}
for n in tests:
    w,h,mtwm,ts,starts=cache[n]; W,H=w*4,h*4
    walk=pb.walkf(w,h,mtwm,ts,lambda f,k: 1 if (f is not None and (f[k]&1)) else 0)
    row=[]
    for r in range(0,5):
        wd=dilate(walk,W,H,r)
        labs,ok=conn(wd,W,H,starts)
        row.append("r%d:%s"%(r, "Y" if ok else "n"))
    print("%-40s %s" % (os.path.basename(n), "  ".join(row)))

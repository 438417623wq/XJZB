import os, sys
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_v216bits as pb

def fill_holes(walk,W,H):
    out=bytearray(walk)
    outside=bytearray(W*H)
    q=deque()
    for x in range(W):
        for y in (0,H-1):
            i=y*W+x
            if not out[i] and not outside[i]: outside[i]=1; q.append(i)
    for y in range(H):
        for x in (0,W-1):
            i=y*W+x
            if not out[i] and not outside[i]: outside[i]=1; q.append(i)
    while q:
        p=q.popleft(); x=p%W; y=p//W
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            xx,yy=x+dx,y+dy
            if 0<=xx<W and 0<=yy<H:
                i=yy*W+xx
                if not out[i] and not outside[i]: outside[i]=1; q.append(i)
    filled=0
    for i in range(W*H):
        if not out[i] and not outside[i]: out[i]=1; filled+=1
    return out, filled

def comps(walk,W,H):
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
    return lab,sizes

def near(walk,W,H,x,y):
    for rr in range(0,20):
        for dx in range(-rr,rr+1):
            for dy in range(-rr,rr+1):
                xx,yy=x+dx,y+dy
                if 0<=xx<W and 0<=yy<H and walk[yy*W+xx]: return lab[yy*W+xx]
    return None

tests=[r"maps\(2)The Small Divide.scm", r"maps\ladder\(4)Dire Straits.scm",
       r"maps\ladder\(6)Polaris Prime.scm", r"maps\ladder\(4)Lost Temple.scm",
       r"maps\(4)Blood Bath.scm", r"maps\BroodWar\(4)River Lethe.scx",
       r"maps\BroodWar\(8)Primeval Isles.scx", r"maps\scenario\(4)King of the Hill.scm",
       r"maps\BroodWar\(6)Sapphire Isles.scx", r"maps\(5)Island Hop.scm",
       r"maps\BroodWar\(6)Hypothermia.scx", r"maps\BroodWar\(2)Midnight Lagoon.scx",
       r"maps\ladder\(4)Rivalry.scm", r"maps\(2)Boxer.scm"]
cache={n:pb.raw(n) for n in tests}
for n in tests:
    w,h,mtwm,ts,starts=cache[n]; W,H=w*4,h*4
    walk=pb.walkf(w,h,mtwm,ts,lambda f,k: 1 if (f is not None and (f[k]&1)) else 0)
    fw,filled=fill_holes(walk,W,H)
    global lab
    lab,sizes=comps(fw,W,H)
    labs=[near(fw,W,H,x,y) for x,y in starts]
    ok=len(set(labs))==1
    print("%-40s filled=%5d comps=%4d biggest=%6d(%.0f%%) labs=%s conn=%s" % (
        os.path.basename(n), filled, len(sizes), max(sizes), 100.0*max(sizes)/(W*H),
        labs, ok))

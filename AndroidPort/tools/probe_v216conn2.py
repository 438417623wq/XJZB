import os, sys
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_maps as pm
import probe_v216walkimg as wi

def comps(walk,W,H,diag):
    lab=[-1]*(W*H); c=0
    dirs=[(1,0),(-1,0),(0,1),(0,-1)]
    if diag: dirs+= [(1,1),(1,-1),(-1,1),(-1,-1)]
    for i in range(W*H):
        if walk[i] and lab[i]<0:
            q=deque([i]); lab[i]=c
            while q:
                p=q.popleft(); x=p%W; y=p//W
                for dx,dy in dirs:
                    xx,yy=x+dx,y+dy
                    if 0<=xx<W and 0<=yy<H and walk[yy*W+xx] and lab[yy*W+xx]<0:
                        lab[yy*W+xx]=c; q.append(yy*W+xx)
            c+=1
    return lab,c

def near(walk,W,H,x,y):
    for r in range(0,16):
        for dx in range(-r,r+1):
            for dy in range(-r,r+1):
                xx,yy=x+dx,y+dy
                if 0<=xx<W and 0<=yy<H and walk[yy*W+xx]: return xx,yy
    return None

for name in [r"maps\scenario\(4)King of the Hill.scm", r"maps\ladder\(4)Dire Straits.scm",
             r"maps\(2)The Small Divide.scm", r"maps\ladder\(6)Polaris Prime.scm",
             r"maps\BroodWar\(6)Hypothermia.scx", r"maps\(2)Boxer.scm"]:
    w,h,walk,starts=wi.walk_of(name)
    W,H=w*4,h*4
    for diag in (False,True):
        lab,c=comps(walk,W,H,diag)
        labs=[lab[(lambda n:n[1]*W+n[0])(near(walk,W,H,sx,sy))] for sx,sy in starts]
        print("%-34s diag=%-5s comps=%3d labs=%s conn=%s" % (
            os.path.basename(name),diag,c,labs,len(set(labs))==1))

import os, sys
from collections import deque
sys.path.insert(0,'.')
import probe_v216bits as pb

def walk_all(w,h,mtwm,ts):
    walk=bytearray(w*4*h*4)
    for ty in range(h):
        for tx in range(w):
            r0=mtwm[ty*w+tx]; grp=(r0&0x7FF0)>>4; var=r0&0xF
            if grp>=len(ts["cv5_tiles"]): grp=0
            vx4m=ts["cv5_tiles"][grp][var]
            if vx4m>=len(ts["vx4_refs"]): vx4m=0
            flags=ts["vf4_flags"][vx4m] if vx4m<len(ts["vf4_flags"]) else None
            for k in range(16):
                walk[(ty*4+(k//4))*(w*4)+(tx*4+(k%4))]=1 if (flags is not None and (flags[k]&1)) else 0
    return walk

def dilate(walk,W,H,r):
    if r==0: return bytearray(walk)
    out=bytearray(W*H)
    for y in range(H):
        for x in range(W):
            if walk[y*W+x]:
                for dy in range(-r,r+1):
                    yy=y+dy
                    if 0<=yy<H:
                        for dx in range(-r,r+1):
                            xx=x+dx
                            if 0<=xx<W: out[yy*W+xx]=1
    return out

def fill(walk,W,H):
    out=bytearray(walk); seen=bytearray(W*H); q=deque()
    for x in range(W):
        for y in (0,H-1):
            i=y*W+x
            if not out[i] and not seen[i]: seen[i]=1; q.append(i)
    for y in range(H):
        for x in (0,W-1):
            i=y*W+x
            if not out[i] and not seen[i]: seen[i]=1; q.append(i)
    while q:
        p=q.popleft(); x=p%W; y=p//W
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            xx,yy=x+dx,y+dy
            if 0<=xx<W and 0<=yy<H:
                i=yy*W+xx
                if not out[i] and not seen[i]: seen[i]=1; q.append(i)
    for i in range(W*H):
        if not out[i] and not seen[i]: out[i]=1
    return out

def conn8(walk,W,H,starts):
    lab=[-1]*(W*H); c=0
    dirs=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
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
    def near(x,y):
        for rr in range(0,32):
            for dx in range(-rr,rr+1):
                for dy in range(-rr,rr+1):
                    xx,yy=x+dx,y+dy
                    if 0<=xx<W and 0<=yy<H and walk[yy*W+xx]: return lab[yy*W+xx]
        return None
    labs=[near(x,y) for x,y in starts]
    return labs, (len(starts)>=2 and None not in labs and len(set(labs))==1)

def minr(path):
    w,h,mtwm,ts,starts=pb.raw(path); W,H=w*4,h*4
    base=walk_all(w,h,mtwm,ts)
    for r in range(0,9):
        wk=fill(dilate(base,W,H,r),W,H)
        labs,ok=conn8(wk,W,H,starts)
        if ok: return r,None
    return None,labs

tests=[('(4)Dire Straits.scm',r"maps\ladder\(4)Dire Straits.scm"),
 ('(6)Polaris Prime.scm',r"maps\ladder\(6)Polaris Prime.scm"),
 ('(6)Hypothermia.scx',r"maps\BroodWar\(6)Hypothermia.scx"),
 ('(8)StarCraft Fortress.scm',r"maps\scenario\(8)StarCraft Fortress.scm"),
 ('(2)The Small Divide.scm',r"maps\(2)The Small Divide.scm"),
 ('(5)Island Hop.scm',r"maps\(5)Island Hop.scm"),
 ('(6)Sapphire Isles.scx',r"maps\BroodWar\(6)Sapphire Isles.scx"),
 ('(8)Primeval Isles.scx',r"maps\BroodWar\(8)Primeval Isles.scx"),
 ('(4)Lost Temple.scm',r"maps\ladder\(4)Lost Temple.scm"),
 ('(8)Frozen Sea.scx',r"maps\BroodWar\(8)Frozen Sea.scx"),
 ('(6)Thin Ice.scx',r"maps\BroodWar\(6)Thin Ice.scx"),
 ('(4)Blood Bath.scm',r"maps\(4)Blood Bath.scm"),
 ('(8)The Hunters.scm',r"maps\(8)The Hunters.scm")]
for name,path in tests:
    r,labs=minr(path)
    print('%-32s min_dilation=%s labs=%s' % (name, r if r is not None else '>8', labs))

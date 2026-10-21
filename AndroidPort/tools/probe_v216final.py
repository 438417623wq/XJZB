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
    out=bytearray(walk); out_=bytearray(W*H); q=deque()
    for x in range(W):
        for y in (0,H-1):
            i=y*W+x
            if not out[i] and not out_[i]: out_[i]=1; q.append(i)
    for y in range(H):
        for x in (0,W-1):
            i=y*W+x
            if not out[i] and not out_[i]: out_[i]=1; q.append(i)
    while q:
        p=q.popleft(); x=p%W; y=p//W
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            xx,yy=x+dx,y+dy
            if 0<=xx<W and 0<=yy<H:
                i=yy*W+xx
                if not out[i] and not out_[i]: out_[i]=1; q.append(i)
    for i in range(W*H):
        if not out[i] and not out_[i]: out[i]=1
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
        for rr in range(0,24):
            for dx in range(-rr,rr+1):
                for dy in range(-rr,rr+1):
                    xx,yy=x+dx,y+dy
                    if 0<=xx<W and 0<=yy<H and walk[yy*W+xx]: return lab[yy*W+xx]
        return None
    labs=[near(x,y) for x,y in starts]
    return labs, (len(starts)>=2 and None not in labs and len(set(labs))==1)

tests=[('(4)Lost Temple.scm',r"maps\ladder\(4)Lost Temple.scm"),('(4)Dire Straits.scm',r"maps\ladder\(4)Dire Straits.scm"),
 ('(4)Rivalry.scm',r"maps\ladder\(4)Rivalry.scm"),('(4)Ashrigo.scm',r"maps\ladder\(4)Ashrigo.scm"),
 ('(6)Polaris Prime.scm',r"maps\ladder\(6)Polaris Prime.scm"),('(6)Acropolis.scm',r"maps\ladder\(6)Acropolis.scm"),
 ('(4)Proving Grounds.scm',r"maps\ladder\(4)Proving Grounds.scm"),
 ('(8)Frozen Sea.scx',r"maps\BroodWar\(8)Frozen Sea.scx"),('(6)Hypothermia.scx',r"maps\BroodWar\(6)Hypothermia.scx"),
 ('(6)Thin Ice.scx',r"maps\BroodWar\(6)Thin Ice.scx"),('(4)Scorched Earth.scx',r"maps\BroodWar\(4)Scorched Earth.scx"),
 ('(6)Sirocco.scx',r"maps\BroodWar\(6)Sirocco.scx"),('(4)Wasteland.scx',r"maps\BroodWar\(4)Wasteland.scx"),
 ('(4)Nightfall.scx',r"maps\BroodWar\(4)Nightfall.scx"),('(4)Sanctuary.scx',r"maps\BroodWar\(4)Sanctuary.scx"),
 ('(6)Azure Plains.scx',r"maps\BroodWar\(6)Azure Plains.scx"),('(6)Close Encounters.scx',r"maps\BroodWar\(6)Close Encounters.scx"),
 ('(7)Broken Steppes.scm',r"maps\BroodWar\(7)Broken Steppes.scm"),('(8)Theatre of War.scm',r"maps\BroodWar\(8)Theatre of War.scm"),
 ('(8)Tribes.scm',r"maps\BroodWar\(8)Tribes.scm"),('(8)Jungle Rumble.scm',r"maps\(8)Jungle Rumble.scm"),
 ('(8)Killing Fields.scm',r"maps\(8)Killing Fields.scm"),('(8)Plains of Snow 98.scm',r"maps\(8)Plains of Snow '98.scm"),
 ('(8)River Runs Through It.scm',r"maps\(8)River Runs Through It.scm"),('(4)King of the Hill.scm',r"maps\scenario\(4)King of the Hill.scm"),
 ('(8)StarCraft Fortress.scm',r"maps\scenario\(8)StarCraft Fortress.scm"),('(4)Zergling Round-Up.scm',r"maps\scenario\(4)Zergling Round-Up.scm"),
 ('(4)River Lethe.scx',r"maps\BroodWar\(4)River Lethe.scx"),
 # islands + shipped
 ('(5)Island Hop.scm',r"maps\(5)Island Hop.scm"),('(6)Sapphire Isles.scx',r"maps\BroodWar\(6)Sapphire Isles.scx"),
 ('(8)Primeval Isles.scx',r"maps\BroodWar\(8)Primeval Isles.scx"),('(2)The Small Divide.scm',r"maps\(2)The Small Divide.scm"),
 ('(2)Volcanis.scm',r"maps\(2)Volcanis.scm"),('(4)Blood Bath.scm',r"maps\(4)Blood Bath.scm"),
 ('(2)Boxer.scm',r"maps\(2)Boxer.scm"),('(8)The Hunters.scm',r"maps\(8)The Hunters.scm"),
 ('(2)Bottleneck.scm',r"maps\(2)Bottleneck.scm"),('(3)Three Kingdoms.scm',r"maps\(3)Three Kingdoms.scm"),
 ('(2)River Crossing.scm',r"maps\(2)River Crossing.scm"),('(4)Cyclone.scm',r"maps\(4)Cyclone.scm"),
 ('(4)Dark Crystal.scm',r"maps\(4)Dark Crystal.scm")]
for name,path in tests:
    try: w,h,mtwm,ts,starts=pb.raw(path)
    except Exception as e: print('%-34s ERR' % name); continue
    W,H=w*4,h*4
    for r in (0,1):
        wk=fill(dilate(walk_all(w,h,mtwm,ts),W,H,r),W,H)
        labs,ok=conn8(wk,W,H,starts)
        if r==1: print('%-34s r=%d conn=%-5s labs=%s' % (name,r,ok,labs))

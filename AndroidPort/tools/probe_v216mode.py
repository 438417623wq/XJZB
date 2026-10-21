import os, sys
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_v216bits as pb

def walk_mode(w,h,mtwm,ts,mode):
    walk=bytearray(w*4*h*4)
    for ty in range(h):
        for tx in range(w):
            r0=mtwm[ty*w+tx]; grp=(r0&0x7FF0)>>4; var=r0&0xF
            if grp>=len(ts["cv5_tiles"]): grp=0
            vx4m=ts["cv5_tiles"][grp][var]
            if vx4m>=len(ts["vx4_refs"]): vx4m=0
            flags=ts["vf4_flags"][vx4m] if vx4m<len(ts["vf4_flags"]) else None
            for k in range(16):
                if flags is None: wk=0
                elif mode=="any": wk=1 if flags[k]!=0 else 0
                else: wk=1 if (flags[k]&1) else 0
                walk[(ty*4+(k//4))*(w*4)+(tx*4+(k%4))]=wk
    return walk

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
        for rr in range(0,24):
            for dx in range(-rr,rr+1):
                for dy in range(-rr,rr+1):
                    xx,yy=x+dx,y+dy
                    if 0<=xx<W and 0<=yy<H and walk[yy*W+xx]: return lab[yy*W+xx]
        return None
    labs=[near(x,y) for x,y in starts]
    return labs, (len(starts)>=2 and len(set(labs))==1 and None not in labs)

names=[
 r"maps\ladder\(4)Lost Temple.scm", r"maps\ladder\(4)Dire Straits.scm",
 r"maps\ladder\(4)Rivalry.scm", r"maps\ladder\(4)Ashrigo.scm",
 r"maps\ladder\(6)Polaris Prime.scm", r"maps\ladder\(6)Acropolis.scm",
 r"maps\ladder\(4)Proving Grounds.scm",
 r"maps\BroodWar\(8)Frozen Sea.scx", r"maps\BroodWar\(6)Hypothermia.scx",
 r"maps\BroodWar\(6)Thin Ice.scx", r"maps\BroodWar\(4)Scorched Earth.scx",
 r"maps\BroodWar\(6)Sirocco.scx", r"maps\BroodWar\(4)Wasteland.scx",
 r"maps\BroodWar\(4)Nightfall.scx", r"maps\BroodWar\(4)Sanctuary.scx",
 r"maps\BroodWar\(6)Azure Plains.scx", r"maps\BroodWar\(6)Close Encounters.scx",
 r"maps\BroodWar\(7)Broken Steppes.scm", r"maps\BroodWar\(8)Theatre of War.scm",
 r"maps\BroodWar\(8)Tribes.scm", r"maps\(8)Jungle Rumble.scm",
 r"maps\(8)Killing Fields.scm", r"maps\(8)Plains of Snow '98.scm",
 r"maps\(8)River Runs Through It.scm", r"maps\scenario\(4)King of the Hill.scm",
 r"maps\scenario\(8)StarCraft Fortress.scm", r"maps\scenario\(4)Zergling Round-Up.scm",
 r"maps\BroodWar\(4)River Lethe.scx",
 # islands / known disconnected
 r"maps\(5)Island Hop.scm", r"maps\BroodWar\(6)Sapphire Isles.scx",
 r"maps\BroodWar\(8)Primeval Isles.scx", r"maps\(2)The Small Divide.scm",
 r"maps\(4)Blood Bath.scm", r"maps\(2)Boxer.scm", r"maps\(8)The Hunters.scm",
]
for n in names:
    try:
        w,h,mtwm,ts,starts=pb.raw(n)
    except Exception as e:
        print("%-42s ERR %s" % (os.path.basename(n), e)); continue
    W,H=w*4,h*4
    res=[]
    for mode in ("any","all"):
        labs,ok=conn(walk_mode(w,h,mtwm,ts,mode),W,H,starts)
        res.append("%s=%s" % (mode,"Y" if ok else "n"))
    print("%-42s %s" % (os.path.basename(n), "  ".join(res)))

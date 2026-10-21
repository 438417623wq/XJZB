import os, sys
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe_v216bits as pb

def mega_walk(w,h,mtwm,ts,mode):
    walk=bytearray(w*4*h*4)
    for ty in range(h):
        for tx in range(w):
            r0=mtwm[ty*w+tx]; grp=(r0&0x7FF0)>>4; var=r0&0xF
            if grp>=len(ts["cv5_tiles"]): grp=0
            vx4m=ts["cv5_tiles"][grp][var]
            if vx4m>=len(ts["vx4_refs"]): vx4m=0
            flags=ts["vf4_flags"][vx4m] if vx4m<len(ts["vf4_flags"]) else None
            for k in range(16):
                if mode=="any": wk=1 if (flags is not None and flags[k]!=0) else 0
                elif mode=="all": wk=1 if (flags is not None and (flags[k]&1)) else 0
                else: wk=1 if (flags is not None and (flags[k]&1)) else 0
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
    return c, (max(sizes) if sizes else 0), 100.0*(max(sizes) if sizes else 0)/(W*H)

tests=[r"maps\(2)The Small Divide.scm", r"maps\ladder\(4)Dire Straits.scm",
       r"maps\ladder\(6)Polaris Prime.scm", r"maps\ladder\(4)Lost Temple.scm",
       r"maps\(4)Blood Bath.scm", r"maps\BroodWar\(4)River Lethe.scx",
       r"maps\BroodWar\(8)Primeval Isles.scx", r"maps\scenario\(4)King of the Hill.scm",
       r"maps\BroodWar\(6)Sapphire Isles.scx", r"maps\(5)Island Hop.scm"]
cache={n:pb.raw(n) for n in tests}
for n in tests:
    w,h,mtwm,ts,starts=cache[n]; W,H=w*4,h*4
    out=[]
    for mode in ("any","all"):
        walk=mega_walk(w,h,mtwm,ts,mode)
        c,big,frac=stats(walk,W,H,starts)
        out.append("%s comps=%3d big=%.0f%%" % (mode,c,frac))
    print("%-40s %s" % (os.path.basename(n), "  |  ".join(out)))

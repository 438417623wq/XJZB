import os, sys
from collections import deque
sys.path.insert(0,'.')
import probe_v216bits as pb

def walk_idx(w,h,mtwm,ts,which,mode):
    walk=bytearray(w*4*h*4)
    for ty in range(h):
        for tx in range(w):
            r0=mtwm[ty*w+tx]; grp=(r0&0x7FF0)>>4; var=r0&0xF
            if grp>=len(ts["cv5_tiles"]): grp=0
            vx4m=ts["cv5_tiles"][grp][var]
            if vx4m>=len(ts["vx4_refs"]): vx4m=0
            refs=ts["vx4_refs"][vx4m]
            if which=="vx4m": idx=vx4m
            elif which=="grp": idx=grp
            elif which=="vri": idx=refs[0]>>1
            flags=ts["vf4_flags"][idx] if idx<len(ts["vf4_flags"]) else None
            for k in range(16):
                if flags is None: wk=0
                elif mode=="any": wk=1 if flags[k]!=0 else 0
                else: wk=1 if (flags[k]&1) else 0
                walk[(ty*4+(k//4))*(w*4)+(tx*4+(k%4))]=wk
    return walk

def conn(walk,W,H,starts):
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
    return labs, len(set(labs))==1, c, (max(sizes) if sizes else 0)

names=[r"maps\ladder\(4)Dire Straits.scm", r"maps\ladder\(4)Lost Temple.scm",
       r"maps\(8)The Hunters.scm", r"maps\(5)Island Hop.scm", r"maps\(2)The Small Divide.scm"]
cache={n:pb.raw(n) for n in names}
for n in names:
    w,h,mtwm,ts,starts=cache[n]; W,H=w*4,h*4
    print("===",os.path.basename(n))
    for which in ("vx4m","grp"):
        for mode in ("any","all"):
            labs,ok,c,big=conn(walk_idx(w,h,mtwm,ts,which,mode),W,H,starts)
            print("   %-5s %-4s comps=%4d big=%.0f%% labs=%s conn=%s" % (
                which,mode,c,100.0*big/(W*H),labs,ok))

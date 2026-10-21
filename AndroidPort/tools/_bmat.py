import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sc_archive, grp as grpm
ROOT=r"F:\KF\XJZB"
SD=sc_archive.Archive(os.path.join(ROOT,"StarDat.mpq")); BD=sc_archive.Archive(os.path.join(ROOT,"BrooDat.mpq")); PT=sc_archive.Archive(os.path.join(ROOT,"patch_rt.mpq"))
def load(p):
    for ar in (PT,SD,BD):
        if ar.has(p):
            d,g=ar.read_with_gaps(p); return grpm.decode_grp(d,g)
def canvas(f):
    w,h=f["w"],f["h"]; return f["px"],w,h
def diff(a,b):
    pa,wa,ha=canvas(a); pb,wb,hb=canvas(b)
    W=max(wa,wb); H=max(ha,hb)
    oa=((W-wa)//2,(H-ha)//2); ob=((W-wb)//2,(H-hb)//2)
    s=0.0; n=0
    for y in range(H):
        for x in range(W):
            ia=ia2=255
            ax=x-oa[0]; ay=y-oa[1]
            if 0<=ax<wa and 0<=ay<ha:
                i=(ay*wa+ax)*4
                if pa[i+3]!=0: ia=pa[i]; ia2=pa[i+2]
            bx=x-ob[0]; by=y-ob[1]
            ib=ib2=255
            if 0<=bx<wb and 0<=by<hb:
                j=(by*wb+bx)*4
                if pb[j+3]!=0: ib=pb[j]; ib2=pb[j+2]
            if ia==255 and ib==255: continue
            s+=abs(ia-ib)+abs(ia2-ib2); n+=1
    return s/n if n else 0.0
def blockframes(frames,i):
    st=i*17; return frames[st:st+17]
for key,path in (("medic","unit\\terran\\medic.grp"),("broodling","unit\\zerg\\brood.grp")):
    frames,mw,mh=load(path)
    nb=len(frames)//17
    B=[blockframes(frames,i) for i in range(nb)]
    print("=== %s nb=%d ==="%(key,nb))
    M=[[0.0]*nb for _ in range(nb)]
    for i in range(nb):
        for j in range(i+1,nb):
            ds=[diff(B[i][d],B[j][d]) for d in range(17)]
            v=sum(ds)/len(ds)
            M[i][j]=M[j][i]=v
    print("     "+" ".join("%5d"%j for j in range(nb)))
    for i in range(nb):
        print("b%-3d "%i+" ".join("%5d"%round(M[i][j]) for j in range(nb)))
    print("-- nearest 3 per block (mean over 17 dirs) --")
    for i in range(nb):
        r=sorted(range(nb),key=lambda j:(M[i][j] if j!=i else 1e9))[:3]
        print("  b%-2d -> "%i+" ".join("b%d:%d"%(j,round(M[i][j])) for j in r))
    print()

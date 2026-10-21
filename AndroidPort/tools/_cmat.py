import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sc_archive, grp as grpm
from PIL import Image
ROOT=r"F:\KF\XJZB"
SD=sc_archive.Archive(os.path.join(ROOT,"StarDat.mpq")); BD=sc_archive.Archive(os.path.join(ROOT,"BrooDat.mpq")); PT=sc_archive.Archive(os.path.join(ROOT,"patch_rt.mpq"))
def load(p):
    for ar in (PT,SD,BD):
        if ar.has(p):
            d,g=ar.read_with_gaps(p); return grpm.decode_grp(d,g)
def cell(f,mw,mh):
    """place frame at its true offset in the full GRP cell -> stable body position"""
    im=Image.new("L",(mw,mh),255)   # 255 = transparent sentinel
    px=im.load(); src=f["px"]; w=f["w"]; h=f["h"]; ox=f["x"]; oy=f["y"]
    for y in range(h):
        b=y*w
        for x in range(w):
            v=src[b+x]
            if v!=255: px[ox+x,oy+y]=v
    return im
def cdiff(a,b):
    pa,pb=a.load(),b.load(); W,H=a.size; s=0;n=0
    for y in range(H):
        for x in range(W):
            va=pa[x,y]; vb=pb[x,y]
            if va==255 and vb==255: continue
            if va==255: va=0
            if vb==255: vb=0
            s+=abs(va-vb); n+=1
    return s/n if n else 0.0
for key,path in (("medic","unit\\terran\\medic.grp"),("marine","unit\\terran\\marine.grp")):
    frames,mw,mh=load(path); nb=len(frames)//17
    print("=== %s n=%d nb=%d cell=%dx%d  [CELL-FIXED, dir 0 / dir 8 / avg] ==="%(key,len(frames),nb,mw,mh))
    def mat(dd):
        B=[[cell(frames[i*17+d],mw,mh) for d in range(17)] for i in range(nb)]
        M=[[0.0]*nb for _ in range(nb)]
        for i in range(nb):
            for j in range(i+1,nb):
                v=sum(cdiff(B[i][d],B[j][d]) for d in range(17))/17.0
                M[i][j]=M[j][i]=v
        return M
    M=mat(0)
    print("      "+"".join("%6d"%j for j in range(nb)))
    for i in range(nb):
        print("b%-4d "%i+"".join("%6d"%round(M[i][j]) for j in range(nb)))
    print("-- nearest 3 (cell-fixed, 17 dirs averaged) --")
    for i in range(nb):
        r=sorted([j for j in range(nb) if j!=i],key=lambda j:M[i][j])[:3]
        print("  b%-2d -> "%i+" ".join("b%d:%d"%(j,round(M[i][j])) for j in r))
    print()

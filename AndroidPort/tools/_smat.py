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
    im=Image.new("L",(mw,mh),255); px=im.load(); src=f["px"]; w=f["w"];h=f["h"];ox=f["x"];oy=f["y"]
    for y in range(h):
        b=y*w
        for x in range(w):
            v=src[b+x]
            if v!=255: px[ox+x,oy+y]=v
    return im
def cd(a,b):
    pa,pb=a.load(),b.load(); W,H=a.size; s=0;n=0
    for y in range(H):
        for x in range(W):
            va=pa[x,y]; vb=pb[x,y]
            if va==255 and vb==255: continue
            if va==255: va=0
            if vb==255: vb=0
            s+=abs(va-vb); n+=1
    return s/n if n else 0.0
for key,path in (("lurk_egg","unit\\zerg\\LurkEgg.grp"),("spider","unit\\terran\\Spider.grp"),("valkyrie","unit\\terran\\bomber.grp")):
    frames,mw,mh=load(path); n=len(frames)
    C=[cell(f,mw,mh) for f in frames]
    print("=== %s n=%d cell=%dx%d ==="%(key,n,mw,mh))
    print("      "+"".join("%5d"%j for j in range(n)))
    for i in range(n):
        print("f%-4d "%i+"".join("%5d"%round(cd(C[i],C[j])) for j in range(n)))
    print("-- nearest 3 --")
    for i in range(n):
        r=sorted([j for j in range(n) if j!=i],key=lambda j:cd(C[i],C[j]))[:3]
        print("  f%-3d -> "%i+" ".join("f%d:%d"%(j,round(cd(C[i],C[j]))) for j in r))
    print()

import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sc_archive, grp as grpm
from PIL import Image
ROOT=r"F:\KF\XJZB"
SD=sc_archive.Archive(os.path.join(ROOT,"StarDat.mpq")); BD=sc_archive.Archive(os.path.join(ROOT,"BrooDat.mpq")); PT=sc_archive.Archive(os.path.join(ROOT,"patch_rt.mpq"))
wpe,_=SD.read_with_gaps("tileset\\jungle.wpe")
PAL=[(wpe[i*4],wpe[i*4+1],wpe[i*4+2]) for i in range(256)]
def load(p):
    for ar in (PT,SD,BD):
        if ar.has(p):
            d,g=ar.read_with_gaps(p); return grpm.decode_grp(d,g)
def fimg(f):
    im=Image.new("RGBA",(f["w"],f["h"]),(0,0,0,0)); px=im.load(); src=f["px"]
    for y in range(f["h"]):
        b=y*f["w"]
        for x in range(f["w"]):
            v=src[b+x]
            if v!=255: px[x,y]=PAL[v]+(255,)
    return im
def tight(f):
    im=fimg(f); bb=im.getbbox(); return im.crop(bb) if bb else None
def diff(a,b):
    if a is None and b is None: return 0.0
    if a is None or b is None: return 255.0
    w,h=max(a.width,b.width),max(a.height,b.height)
    ca=Image.new("RGBA",(w,h),(0,0,0,0)); cb=Image.new("RGBA",(w,h),(0,0,0,0))
    ca.paste(a,((w-a.width)//2,(h-a.height)//2),a); cb.paste(b,((w-b.width)//2,(h-b.height)//2),b)
    pa,pb=ca.load(),cb.load(); tot=0
    for y in range(h):
        for x in range(w):
            ra,ga,ba,aa=pa[x,y]; rb,gb,bb2,ab=pb[x,y]
            if aa==0 and ab==0: continue
            tot+=abs(ra-rb)+abs(ga-gb)+abs(ba-bb2)+abs(aa-ab)
    return tot/(3.0*w*h)
for key,path in (("medic","unit\\terran\\medic.grp"),("broodling","unit\\zerg\\brood.grp")):
    frames,mw,mh=load(path); nb=len(frames)//17
    B=[[frames[i*17+d] for d in range(17)] for i in range(nb)]
    print("=== %s nb=%d (all 17 dirs averaged) ==="%(key,nb))
    M=[[0.0]*nb for _ in range(nb)]
    for i in range(nb):
        for j in range(i+1,nb):
            v=sum(diff(tight(B[i][d]),tight(B[j][d])) for d in range(17))/17.0
            M[i][j]=M[j][i]=v
    print("      "+"".join("%6d"%j for j in range(nb)))
    for i in range(nb):
        print("b%-4d "%i+"".join("%6d"%round(M[i][j]) for j in range(nb)))
    print("-- nearest 3 --")
    for i in range(nb):
        r=sorted([j for j in range(nb) if j!=i],key=lambda j:M[i][j])[:3]
        print("  b%-2d -> "%i+" ".join("b%d:%d"%(j,round(M[i][j])) for j in r))
    print()

import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sc_archive, grp as grpm
from PIL import Image
ROOT=r"F:\KF\XJZB"
SD=sc_archive.Archive(os.path.join(ROOT,"StarDat.mpq")); BD=sc_archive.Archive(os.path.join(ROOT,"BrooDat.mpq")); PT=sc_archive.Archive(os.path.join(ROOT,"patch_rt.mpq"))
wpe,_=SD.read_with_gaps("tileset\\jungle.wpe"); PAL=[(wpe[i*4],wpe[i*4+1],wpe[i*4+2]) for i in range(256)]
def load(p):
    for ar in (PT,SD,BD):
        if ar.has(p):
            d,g=ar.read_with_gaps(p); return grpm.decode_grp(d,g)
def fi(f):
    im=Image.new("RGBA",(f["w"],f["h"]),(0,0,0,0)); px=im.load(); s=f["px"]
    for y in range(f["h"]):
        b=y*f["w"]
        for x in range(f["w"]):
            v=s[b+x]
            if v!=255: px[x,y]=PAL[v]+(255,)
    return im
# brood: exact duplicate structure -- which frame indices are byte-identical
frames,_,_=load("unit\\zerg\\brood.grp"); n=len(frames)
print("brood n=%d"%n)
groups=[]
seen={}
for i,f in enumerate(frames):
    k=(f["w"],f["h"],bytes(f["px"]))
    seen.setdefault(k,[]).append(i)
print("distinct images: %d"%len(seen))
for k,v in sorted(seen.items(), key=lambda t:t[1][0]):
    print("  w=%d h=%d  frames %s"%(k[0],k[1],v))

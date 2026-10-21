import os, sc_archive, grp as grpm
from PIL import Image
ROOT = r"F:\KF\XJZB"; OUT = ROOT + r"\AndroidPort\tools\out"
SD = sc_archive.Archive(ROOT + r"\StarDat.mpq")
BD = sc_archive.Archive(ROOT + r"\BrooDat.mpq")
PT = sc_archive.Archive(ROOT + r"\patch_rt.mpq")
wpe,_ = SD.read_with_gaps(r"tileset\jungle.wpe")
PAL = [(wpe[i*4], wpe[i*4+1], wpe[i*4+2]) for i in range(256)]
def dec(p):
    for a in (PT,SD,BD):
        if a.has(p):
            d,g = a.read_with_gaps(p)
            return grpm.decode_grp(d,g)
def img(f):
    im = Image.new("RGBA",(f["w"],f["h"]),(0,0,0,0)); px = im.load(); s = f["px"]
    for y in range(f["h"]):
        b = y*f["w"]
        for x in range(f["w"]):
            v = s[b+x]
            if v != 255: px[x,y] = PAL[v]+(255,)
    return im
def diff(a,b):
    A,B = a["px"], b["px"]; n = min(len(A),len(B))
    return sum(abs(A[i]-B[i]) for i in range(n))/float(n)

fr,_,_ = dec(r"unit\thingy\plasma.grp")
ded = [fr[i] for i in range(0,len(fr),2)]
print("plasma dedup n=%d" % len(ded))
# Is dedup a rotation (17 dirs x 4 steps) or a 68-step animation?
# For dir-layout step*17+dir: frames sharing a step differ by direction only.
# A ball rotating: consecutive dedup frames differ by ~1/17 turn.
for name, idx in [("u,u+1",1),("u,u+2",2),("u,u+4",4),("u,u+8",8),("u,u+17",17),("u,u+34",34)]:
    v = [diff(ded[i],ded[i+idx]) for i in range(0, 24)]
    print("  %-8s mean=%.1f  %s" % (name, sum(v)/len(v), ["%.0f"%x for x in v[:8]]))
# autocorrelation: find the period that minimises diff
best = []
for per in range(1, 35):
    v = [diff(ded[i],ded[i+per]) for i in range(0, min(40, len(ded)-per))]
    best.append((sum(v)/len(v), per))
best.sort()
print("  best periods (lowest mean diff):", [(p, "%.1f"%m) for m,p in best[:6]])

CELL=96; cols=17
rows=(len(ded)+cols-1)//cols
sheet=Image.new("RGBA",(cols*CELL, rows*CELL),(25,25,35,255))
for k,i in enumerate(range(len(ded))):
    im=img(ded[i])
    sc=min(CELL/float(im.width),CELL/float(im.height),1.0)
    if sc!=1.0: im=im.resize((max(1,int(im.width*sc)),max(1,int(im.height*sc))),Image.NEAREST)
    sheet.alpha_composite(im,((k%cols)*CELL+(CELL-im.width)//2,(k//cols)*CELL+(CELL-im.height)//2))
sheet.save(os.path.join(OUT,"cs_plasma_dedup.png"))
print("wrote cs_plasma_dedup.png %dx%d" % sheet.size)

# blastcan: 17 dirs x 1 frame, or 17-step animation?
bf,_,_ = dec(r"unit\bullet\blastcan.grp")
print("blastcan n=%d" % len(bf))
for name, idx in [("u,u+1",1),("u,u+8",8),("u,u+9",9)]:
    v=[diff(bf[i],bf[i+idx]) for i in range(0, min(8,len(bf)-idx))]
    print("  %-8s %s" % (name, ["%.0f"%x for x in v]))

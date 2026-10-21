import os, sc_archive, grp as grpm
from PIL import Image
ROOT = r"F:\KF\XJZB"
OUT  = r"F:\KF\XJZB\AndroidPort\tools\out"
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
    return None
def img(f):
    im = Image.new("RGBA",(f["w"],f["h"]),(0,0,0,0))
    px = im.load(); s = f["px"]
    for y in range(f["h"]):
        b = y*f["w"]
        for x in range(f["w"]):
            v = s[b+x]
            if v != 255: px[x,y] = PAL[v]+(255,)
    return im
def diff(a,b):
    A,B = a["px"], b["px"]; n = min(len(A),len(B))
    return sum(abs(A[i]-B[i]) for i in range(n))/float(n)

r = dec(r"unit\thingy\plasma.grp")
frames, mw, mh = r
print("plasma n=%d" % len(frames))
print("  diff(i,i+1) first 20:", ["%.0f"%diff(frames[i],frames[i+1]) for i in range(20)])
print("  diff(i,i+2) first 20:", ["%.0f"%diff(frames[i],frames[i+2]) for i in range(20)])
uniq = [frames[i] for i in range(0,len(frames),2)]
print("  unique(pair-dedup)=%d" % len(uniq))
print("  uniq diff(u,u+1) first 16:", ["%.0f"%diff(uniq[i],uniq[i+1]) for i in range(16)])
print("  uniq diff(u,u+17) first 16:", ["%.0f"%diff(uniq[i],uniq[i+17]) for i in range(16)])

os.makedirs(OUT, exist_ok=True)
for key, path in [(r"emp", r"unit\thingy\emp.grp"),
                  (r"disrupt", r"unit\thingy\disrupt.grp"),
                  (r"plasma", r"unit\thingy\plasma.grp"),
                  (r"ehamed", r"unit\thingy\ehaMed.grp"),
                  (r"blastcan", r"unit\bullet\blastcan.grp")]:
    rr = dec(path)
    fr, cw, ch = rr
    sel = list(range(0, min(len(fr), 24)))
    CELL = 128
    cols = 8
    rows = (len(sel)+cols-1)//cols
    sheet = Image.new("RGBA",(cols*CELL, rows*CELL),(30,30,40,255))
    for k,i in enumerate(sel):
        im = img(fr[i])
        sc = min(CELL/float(im.width), CELL/float(im.height), 1.0)
        if sc != 1.0:
            im = im.resize((max(1,int(im.width*sc)), max(1,int(im.height*sc))), Image.NEAREST)
        sheet.alpha_composite(im, ((k%cols)*CELL + (CELL-im.width)//2,
                                   (k//cols)*CELL + (CELL-im.height)//2))
    sheet.save(os.path.join(OUT, "cs_%s.png" % key))
    print("wrote cs_%s.png  (n=%d, showing %d)" % (key, len(fr), len(sel)))

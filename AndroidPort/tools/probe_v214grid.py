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

cands = ["emp","empl","plasma","disrupt","ehaMed","eycBlast","eveCast","emsBeam",
         "emsHit","elect02","elect02a","halmind","mushroom","consume","GeySmok1",
         "efgHit","ecaHit","tveGlowB","tveGlowO","tveGlowW","etgHit","ep3Burst"]
print("--- has() census ---")
avail = []
for c in cands:
    p = r"unit\thingy\%s.grp" % c
    w = [n for n,a in (("PT",PT),("SD",SD),("BD",BD)) if a.has(p)]
    print("  %-12s %s" % (c, ",".join(w) or "MISSING"))
    if w: avail.append(c)

CELL=96; cols=8
names = avail
rows = len(names)
sheet = Image.new("RGBA",(cols*CELL, rows*CELL),(25,25,35,255))
for r_i,c in enumerate(names):
    rr = dec(r"unit\thingy\%s.grp" % c)
    fr,cw,ch = rr
    # dedup identical consecutive frames, then take up to 8
    uniq=[fr[0]]
    for f in fr[1:]:
        if f["px"] != uniq[-1]["px"]: uniq.append(f)
    sel = uniq[:cols]
    for k,f in enumerate(sel):
        im = img(f)
        sc = min(CELL/float(im.width), CELL/float(im.height), 1.0)
        if sc != 1.0: im = im.resize((max(1,int(im.width*sc)),max(1,int(im.height*sc))),Image.NEAREST)
        sheet.alpha_composite(im,(k*CELL+(CELL-im.width)//2, r_i*CELL+(CELL-im.height)//2))
    print("  %-12s n=%d uniq=%d cell=%dx%d" % (c, len(fr), len(uniq), cw, ch))
sheet.save(os.path.join(OUT,"cs_thingy_grid.png"))
print("wrote cs_thingy_grid.png %dx%d rows=%s" % (sheet.size[0], sheet.size[1], names))

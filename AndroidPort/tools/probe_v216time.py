import os, sys, time
sys.path.insert(0,'.')
import pipeline_maps as pm
t=time.time()
r=pm.read_chk(os.path.join(pm.ROOT, r"maps\ladder\(4)Lost Temple.scm"))
chk,gaps=r; g,sec=pm.parse_chk(chk,gaps)
off,_=sec[b"DIM "]; w,h=g.u16(off),g.u16(off+2)
print("dims",w,h,"%.2fs"%(time.time()-t)); t=time.time()
eo,_=sec[b"ERA "]; ts=pm.load_tileset(pm.TILESETS[g.byte(eo)])
print("tileset load %.2fs"%(time.time()-t)); t=time.time()
mo,_=sec[b"MTXM"]; mt=[g.u16(mo+i*2) for i in range(w*h)]
print("mtxm %.2fs"%(time.time()-t)); t=time.time()
walk=pm._walk_bitmap(w,h,mt,ts)
print("walk_bitmap %.2fs"%(time.time()-t)); t=time.time()
starts=pm._starts_of(g,sec)
ok,ids=pm.connectivity(walk,starts)
print("connectivity %.2fs ok=%s"%(time.time()-t,ok))

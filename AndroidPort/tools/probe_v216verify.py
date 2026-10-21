import os, sys
sys.path.insert(0,'.')
import numpy as np
import pipeline_maps as pm

def walk_loop(w,h,mtwm,ts):
    walk=bytearray(w*4*h*4)
    for ty in range(h):
        for tx in range(w):
            raw=mtwm[ty*w+tx]; grp=(raw&0x7FF0)>>4; var=raw&0xF
            if grp>=len(ts["cv5_tiles"]): grp=0
            vx4m=ts["cv5_tiles"][grp][var]
            if vx4m>=len(ts["vx4_refs"]): vx4m=0
            flags=ts["vf4_flags"][vx4m] if vx4m<len(ts["vf4_flags"]) else None
            for k in range(16):
                wk=1 if (flags is not None and (flags[k]&0x0001)) else 0
                X4=tx*4+(k%4); Y4=ty*4+(k//4)
                if 0<=X4<w*4 and 0<=Y4<h*4:
                    walk[Y4*(w*4)+X4]=wk
    return np.frombuffer(bytes(walk),dtype=np.uint8).reshape(h*4,w*4)

for n in [r"maps\ladder\(4)Lost Temple.scm", r"maps\ladder\(4)Dire Straits.scm",
          r"maps\(2)Volcanis.scm", r"maps\BroodWar\(8)Frozen Sea.scx",
          r"maps\(8)Killing Fields.scm", r"maps\BroodWar\(4)River Lethe.scx"]:
    r=pm.read_chk(os.path.join(pm.ROOT,n)); chk,gaps=r; g,sec=pm.parse_chk(chk,gaps)
    off,_=sec[b"DIM "]; w,h=g.u16(off),g.u16(off+2)
    mo,_=sec[b"MTXM"]; mt=[g.u16(mo+i*2) for i in range(w*h)]
    eo,_=sec[b"ERA "]; ts=pm.load_tileset(pm.TILESETS[g.byte(eo)])
    a=walk_loop(w,h,mt,ts); b=pm._walk_bitmap(w,h,mt,ts)
    print("%-30s identical=%s diff=%d" % (os.path.basename(n), np.array_equal(a,b), int((a!=b).sum())))

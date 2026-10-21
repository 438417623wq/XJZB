import os, sys
from collections import Counter
sys.path.insert(0,'.')
import pipeline_maps as pm
for n in [r"maps\ladder\(4)Dire Straits.scm", r"maps\ladder\(4)Lost Temple.scm",
          r"maps\(8)The Hunters.scm", r"maps\ladder\(6)Polaris Prime.scm"]:
    r=pm.read_chk(os.path.join(pm.ROOT,n)); chk,gaps=r; g,sec=pm.parse_chk(chk,gaps)
    off,_=sec[b"DIM "]; w,h=g.u16(off),g.u16(off+2)
    mo,_=sec[b"MTXM"]; mt=[g.u16(mo+i*2) for i in range(w*h)]
    ts=pm.load_tileset("jungle" if b"jungle" else "jungle")
    grps=Counter(((v & 0x7FF0)>>4) for v in mt)
    vars_=Counter(v&0xF for v in mt)
    ncv=len(ts["cv5_tiles"]); nvx=len(ts["vx4_refs"]); nvf=len(ts["vf4_flags"])
    over_g=sum(c for k,c in grps.items() if k>=ncv)
    print("%-26s %dx%d ncv5=%d nvx4=%d nvf4=%d over_grp=%d maxgrp=%d grps=%d vars=%s" % (
        os.path.basename(n), w,h,ncv,nvx,nvf, over_g, max(grps), len(grps), sorted(vars_.keys())))
    # how many tiles map to a vx4m that's out of range?
    over_v=0
    for v in mt:
        grp=(v&0x7FF0)>>4; var=v&0xF
        if grp>=ncv: grp=0
        vx4m=ts["cv5_tiles"][grp][var]
        if vx4m>=nvx: over_v+=1
    print("     tiles with vx4m out of range: %d" % over_v)

import os,sys,struct,hashlib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sc_archive
ROOT=r"F:\KF\XJZB"
SD=sc_archive.Archive(os.path.join(ROOT,"StarDat.mpq")); BD=sc_archive.Archive(os.path.join(ROOT,"BrooDat.mpq")); PT=sc_archive.Archive(os.path.join(ROOT,"patch_rt.mpq"))
def raw(p):
    for nm,ar in (("PT",PT),("SD",SD),("BD",BD)):
        if ar.has(p):
            d,g=ar.read_with_gaps(p); return nm,d,g
    return None,None,None
for p in ("unit\\terran\\marine.grp","unit\\terran\\medic.grp"):
    nm,d,g=raw(p)
    fc,mw,mh=struct.unpack_from("<HHH",d,0)
    print("=== %s (%s) fc=%d %dx%d ==="%(p,nm,fc,mw,mh))
    prev=None
    for i in range(0,36):
        base=6+i*8
        x,y,w,h=struct.unpack_from("<BBBB",d,base)
        off=struct.unpack_from("<I",d,base+4)[0]
        # decode px quickly via grp
        print("  f%-3d x=%-3d y=%-3d w=%-3d h=%-3d off=%-6d" % (i,x,y,w,h,off))
    print("  offset deltas (raw u32 fields):", [struct.unpack_from("<I",d,6+i*8+4)[0] for i in range(0,20)])

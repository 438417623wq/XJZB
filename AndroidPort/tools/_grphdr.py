import os,sys,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sc_archive
ROOT=r"F:\KF\XJZB"
SD=sc_archive.Archive(os.path.join(ROOT,"StarDat.mpq")); BD=sc_archive.Archive(os.path.join(ROOT,"BrooDat.mpq")); PT=sc_archive.Archive(os.path.join(ROOT,"patch_rt.mpq"))
def raw(p):
    for nm,ar in (("PT",PT),("SD",SD),("BD",BD)):
        if ar.has(p):
            d,g=ar.read_with_gaps(p); return nm,d
    return None,None
for p in ("unit\\terran\\marine.grp","unit\\terran\\medic.grp","unit\\zerg\\brood.grp","unit\\zerg\\LurkEgg.grp","unit\\terran\\Spider.grp","unit\\terran\\bomber.grp"):
    nm,d=raw(p)
    n,w,h=struct.unpack_from("<HHH",d,0)
    print("%-30s in %s  header frames=%d  %dx%d  bytes=%d" % (p,nm,n,w,h,len(d)))

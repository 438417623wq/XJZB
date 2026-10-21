import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sc_archive, grp as grpm
ROOT=r"F:\KF\XJZB"
SD=sc_archive.Archive(os.path.join(ROOT,"StarDat.mpq")); BD=sc_archive.Archive(os.path.join(ROOT,"BrooDat.mpq")); PT=sc_archive.Archive(os.path.join(ROOT,"patch_rt.mpq"))
for path in ["unit\\zerg\\LurkEgg.grp","unit\\terran\\Spider.grp","unit\\terran\\bomber.grp","unit\\zerg\\brood.grp"]:
    for ar in (PT,SD,BD):
        if ar.has(path):
            data,gaps=ar.read_with_gaps(path); frames,mw,mh=grpm.decode_grp(data,gaps); break
    print("%s  n=%d maxcell=%dx%d"%(path,len(frames),mw,mh))
    for i,f in enumerate(frames):
        nz=sum(1 for p in f["px"] if p!=255)
        print("   f%-3d %3dx%-3d px=%d"%(i,f["w"],f["h"],nz))

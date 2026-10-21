import os,sys,hashlib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sc_archive, grp as grpm
ROOT=r"F:\KF\XJZB"
SD=sc_archive.Archive(os.path.join(ROOT,"StarDat.mpq")); BD=sc_archive.Archive(os.path.join(ROOT,"BrooDat.mpq")); PT=sc_archive.Archive(os.path.join(ROOT,"patch_rt.mpq"))
def load(p):
    for ar in (PT,SD,BD):
        if ar.has(p):
            d,g=ar.read_with_gaps(p); return grpm.decode_grp(d,g)
for key,path in (("lurk_egg","unit\\zerg\\LurkEgg.grp"),("spider","unit\\terran\\Spider.grp"),("valkyrie","unit\\terran\\bomber.grp"),("medic","unit\\terran\\medic.grp")):
    frames,mw,mh=load(path)
    hs=[hashlib.md5(bytes(f["px"])).hexdigest()[:8] for f in frames]
    print(key,"n=",len(frames),"distinct=",len(set(hs)))
    print("   ", " ".join("%d:%s"%(i,h) for i,h in enumerate(hs)))

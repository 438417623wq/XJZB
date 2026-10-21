import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sc_archive, grp as grpm
ROOT=r"F:\KF\XJZB"
SD=sc_archive.Archive(os.path.join(ROOT,"StarDat.mpq")); BD=sc_archive.Archive(os.path.join(ROOT,"BrooDat.mpq")); PT=sc_archive.Archive(os.path.join(ROOT,"patch_rt.mpq"))
def load(p):
    for ar in (PT,SD,BD):
        if ar.has(p):
            d,g=ar.read_with_gaps(p); return grpm.decode_grp(d,g)
frames,mw,mh=load("unit\\terran\\medic.grp")
f=frames[0]
print("keys:",sorted(f.keys()))
for k,v in f.items():
    print(" ",k,type(v).__name__, (len(v) if hasattr(v,"__len__") else v))
print("mw,mh:",mw,mh,"len frames:",len(frames))
print("n=230 -> 13 full blocks (221) + 9 =",13*17+9)

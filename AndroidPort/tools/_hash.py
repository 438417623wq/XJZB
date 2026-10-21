import os,sys,hashlib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sc_archive, grp as grpm
ROOT=r"F:\KF\XJZB"
SD=sc_archive.Archive(os.path.join(ROOT,"StarDat.mpq")); BD=sc_archive.Archive(os.path.join(ROOT,"BrooDat.mpq")); PT=sc_archive.Archive(os.path.join(ROOT,"patch_rt.mpq"))
def load(p):
    for ar in (PT,SD,BD):
        if ar.has(p):
            d,g=ar.read_with_gaps(p); return grpm.decode_grp(d,g)
frames,mw,mh=load("unit\\zerg\\brood.grp")
print("type px:",type(frames[0]["px"]))
print("ids f0..f4:",[id(frames[i]["px"]) for i in range(5)])
hs=[]
for i,f in enumerate(frames):
    hs.append(hashlib.md5(bytes(f["px"])).hexdigest()[:10])
print("hash f0..f8:",hs[:9])
print("hash f14..f20:",hs[14:21])
# how many consecutive duplicates
dup=[i for i in range(len(hs)-1) if hs[i]==hs[i+1]]
print("consecutive-duplicate starts:",len(dup),dup[:30])
print("distinct hashes:",len(set(hs)))

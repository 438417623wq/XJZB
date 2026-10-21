import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import sc_archive, grp as grpm
from PIL import Image
ROOT=r"F:\KF\XJZB"
SD=sc_archive.Archive(os.path.join(ROOT,"StarDat.mpq")); BD=sc_archive.Archive(os.path.join(ROOT,"BrooDat.mpq")); PT=sc_archive.Archive(os.path.join(ROOT,"patch_rt.mpq"))
for n in ("scripts\\iscript.bin","scripts\\iscript.lst","arr\\images.tbl"):
    for nm,ar in (("SD",SD),("BD",BD),("PT",PT)):
        if ar.has(n):
            d,_=ar.read_with_gaps(n); print("FOUND",n,"in",nm,"size",len(d)); break
    else:
        print("missing",n)
# hash marine block0 to test duplicate pattern
def load(p):
    for ar in (PT,SD,BD):
        if ar.has(p):
            d,g=ar.read_with_gaps(p); return grpm.decode_grp(d,g)
import hashlib
frames,mw,mh=load("unit\\terran\\marine.grp")
hs=[hashlib.md5(bytes(f["px"])).hexdigest()[:8] for f in frames[:40]]
print("marine f0..f39:", " ".join("%d:%s"%(i,h) for i,h in enumerate(hs)))

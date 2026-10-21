import os, sys
sys.path.insert(0,'.')
import numpy as np
import pipeline_maps as pm

def load(n):
    r=pm.read_chk(os.path.join(pm.ROOT,n)); chk,gaps=r; g,sec=pm.parse_chk(chk,gaps)
    off,_=sec[b"DIM "]; w,h=g.u16(off),g.u16(off+2)
    mo,_=sec[b"MTXM"]; mt=[g.u16(mo+i*2) for i in range(w*h)]
    eo,_=sec[b"ERA "]; ts=pm.load_tileset(pm.TILESETS[g.byte(eo)])
    walk=pm._walk_bitmap(w,h,mt,ts)
    starts=pm._starts_of(g,sec)
    return walk,starts

tests=[('DireStraits',r"maps\ladder\(4)Dire Straits.scm"),('LostTemple',r"maps\ladder\(4)Lost Temple.scm"),
 ('PolarisPrime',r"maps\ladder\(6)Polaris Prime.scm"),('Acropolis',r"maps\ladder\(6)Acropolis.scm"),
 ('FrozenSea',r"maps\BroodWar\(8)Frozen Sea.scx"),('ThinIce',r"maps\BroodWar\(6)Thin Ice.scx"),
 ('AzurePlains',r"maps\BroodWar\(6)Azure Plains.scx"),('Nightfall',r"maps\BroodWar\(4)Nightfall.scx"),
 ('IslandHop',r"maps\(5)Island Hop.scm"),('SapphireIsles',r"maps\BroodWar\(6)Sapphire Isles.scx"),
 ('PrimevalIsles',r"maps\BroodWar\(8)Primeval Isles.scx"),('Hunters',r"maps\(8)The Hunters.scm"),
 ('BloodBath',r"maps\(4)Blood Bath.scm"),('SmallDivide',r"maps\(2)The Small Divide.scm")]
for name,path in tests:
    walk,starts=load(path)
    row=[]
    for d in range(0,5):
        ok,ids=pm.connectivity(walk,starts,dilate=d)
        row.append("d%d:%s"%(d,"Y" if ok else "n"))
    print("%-16s starts=%d %s" % (name,len(starts),"  ".join(row)))

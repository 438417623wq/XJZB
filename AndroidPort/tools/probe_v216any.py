import os, sys
sys.path.insert(0,'.')
import numpy as np
from collections import deque
import pipeline_maps as pm

def walk_any(w,h,mtwm,ts):
    m=np.asarray(mtwm,dtype=np.uint32).reshape(h,w)
    grp=np.clip((m&0x7FF0)>>4,0,len(ts["cv5_tiles"])-1); var=m&0xF
    tiles=np.asarray(ts["cv5_tiles"],dtype=np.int64)
    vx4m=np.clip(tiles[grp,var],0,len(ts["vf4_flags"])-1)
    f=np.asarray(ts["vf4_flags"],dtype=np.int64)[vx4m].reshape(h,w,4,4)
    return (f!=0).astype(np.uint8).transpose(0,2,1,3).reshape(h*4,w*4)

def load(n):
    r=pm.read_chk(os.path.join(pm.ROOT,n)); chk,gaps=r; g,sec=pm.parse_chk(chk,gaps)
    off,_=sec[b"DIM "]; w,h=g.u16(off),g.u16(off+2)
    mo,_=sec[b"MTXM"]; mt=[g.u16(mo+i*2) for i in range(w*h)]
    eo,_=sec[b"ERA "]; ts=pm.load_tileset(pm.TILESETS[g.byte(eo)])
    return walk_any(w,h,mt,ts), pm._starts_of(g,sec)

def conn(walk,starts,dilate):
    wk=pm._dilate(pm._fill_enclosed(walk),dilate); H,W=wk.shape
    def snap(sx,sy):
        for rr in range(0,40):
            y0,y1=max(0,sy-rr),min(H,sy+rr+1); x0,x1=max(0,sx-rr),min(W,sx+rr+1)
            sub=wk[y0:y1,x0:x1]
            if sub.any():
                ys,xs=np.nonzero(sub); return int(y0+ys[0]),int(x0+xs[0])
        return None
    seeds=[snap(x,y) for x,y in starts]
    if seeds[0] is None: return False,seeds
    seen=np.zeros((H,W),bool); dq=deque([seeds[0]]); seen[seeds[0]]=True
    nb=((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1))
    while dq:
        y,x=dq.popleft()
        for dy,dx in nb:
            yy,xx=y+dy,x+dx
            if 0<=yy<H and 0<=xx<W and wk[yy,xx] and not seen[yy,xx]:
                seen[yy,xx]=True; dq.append((yy,xx))
    return all(s and seen[s] for s in seeds), seeds

tests=[('DireStraits',r"maps\ladder\(4)Dire Straits.scm"),('LostTemple',r"maps\ladder\(4)Lost Temple.scm"),
 ('PolarisPrime',r"maps\ladder\(6)Polaris Prime.scm"),('Acropolis',r"maps\ladder\(6)Acropolis.scm"),
 ('Rivalry',r"maps\ladder\(4)Rivalry.scm"),('Ashrigo',r"maps\ladder\(4)Ashrigo.scm"),
 ('ProvingGrounds',r"maps\ladder\(4)Proving Grounds.scm"),
 ('FrozenSea',r"maps\BroodWar\(8)Frozen Sea.scx"),('ThinIce',r"maps\BroodWar\(6)Thin Ice.scx"),
 ('Hypothermia',r"maps\BroodWar\(6)Hypothermia.scx"),
 ('AzurePlains',r"maps\BroodWar\(6)Azure Plains.scx"),('Sirocco',r"maps\BroodWar\(6)Sirocco.scx"),
 ('Wasteland',r"maps\BroodWar\(4)Wasteland.scx"),('Nightfall',r"maps\BroodWar\(4)Nightfall.scx"),
 ('Sanctuary',r"maps\BroodWar\(4)Sanctuary.scx"),('CloseEncounters',r"maps\BroodWar\(6)Close Encounters.scx"),
 ('ScorchedEarth',r"maps\BroodWar\(4)Scorched Earth.scx"),
 ('IslandHop',r"maps\(5)Island Hop.scm"),('SapphireIsles',r"maps\BroodWar\(6)Sapphire Isles.scx"),
 ('PrimevalIsles',r"maps\BroodWar\(8)Primeval Isles.scx"),
 ('Hunters',r"maps\(8)The Hunters.scm"),('BloodBath',r"maps\(4)Blood Bath.scm"),
 ('SmallDivide',r"maps\(2)The Small Divide.scm"),('Boxer',r"maps\(2)Boxer.scm"),
 ('RiverLethe',r"maps\BroodWar\(4)River Lethe.scx"),
 ('StarCraftFortress',r"maps\scenario\(8)StarCraft Fortress.scm"),
 ('ZerglingRoundUp',r"maps\scenario\(4)Zergling Round-Up.scm"),
 ('KingOfTheHill',r"maps\scenario\(4)King of the Hill.scm")]
for name,path in tests:
    walk,starts=load(path)
    row=[]
    for d in (0,1,2):
        ok,_=conn(walk,starts,d)
        row.append("d%d:%s"%(d,"Y" if ok else "n"))
    print("%-18s st=%d %s" % (name,len(starts),"  ".join(row)))

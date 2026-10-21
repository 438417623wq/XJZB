import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_maps as pm

cands = [
 r"maps\ladder\(4)Lost Temple.scm", r"maps\ladder\(4)Dire Straits.scm",
 r"maps\ladder\(4)Rivalry.scm", r"maps\ladder\(4)Ashrigo.scm",
 r"maps\ladder\(6)Polaris Prime.scm", r"maps\ladder\(6)Acropolis.scm",
 r"maps\ladder\(4)Proving Grounds.scm",
 r"maps\BroodWar\(8)Frozen Sea.scx", r"maps\BroodWar\(6)Hypothermia.scx",
 r"maps\BroodWar\(6)Thin Ice.scx", r"maps\BroodWar\(4)Scorched Earth.scx",
 r"maps\BroodWar\(6)Sirocco.scx", r"maps\BroodWar\(6)Cauldron.scx",
 r"maps\BroodWar\(4)Nightfall.scx", r"maps\BroodWar\(4)River Lethe.scx",
 r"maps\BroodWar\(6)Sapphire Isles.scx",
 r"maps\BroodWar\WebMaps\(8)Big Game Hunters.scm",
 r"maps\scenario\(4)King of the Hill.scm", r"maps\scenario\(8)StarCraft Fortress.scm",
 r"maps\scenario\(4)Zergling Round-Up.scm",
]
for c in cands:
    r = pm.read_chk(os.path.join(pm.ROOT, c))
    if not r:
        print("%-52s NO-CHK" % os.path.basename(c)); continue
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    if b"DIM " not in sec or b"ERA " not in sec:
        print("%-52s NO-DIM" % os.path.basename(c)); continue
    off,_ = sec[b"DIM "]; w,h = g.u16(off), g.u16(off+2)
    eoff,_ = sec[b"ERA "]; era = g.byte(eoff)
    ts = pm.TILESETS.get(era, "?%d" % era)
    dd = b"DD2 " in sec or b"DDDATA" in sec
    print("%-52s %3dx%-3d era=%d ts=%-9s dd=%s" % (os.path.basename(c), w, h, era, ts, dd))

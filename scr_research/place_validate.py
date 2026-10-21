import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm
D = r"F:\KF\XJZB\scr_research\tileset"
TILESETS = {0:"badlands",1:"platform",2:"install",3:"ashworld",4:"jungle",5:"desert",6:"ice",7:"twilight"}

def load(p):
    chk, gaps = pm.read_chk(p)
    g, sec = pm.parse_chk(chk, gaps)
    o, s = sec[b"DIM "]; dim = g.bytes_at(o, s); w = dim[0]|dim[1]<<8; h = dim[2]|dim[3]<<8
    o, s = sec[b"ERA "]; era = g.bytes_at(o, s)[0]
    o, s = sec[b"MTXM"]; mt = struct.unpack_from("<%dH" % (s//2), g.bytes_at(o, s), 0)
    o, s = sec[b"DD2 "]; raw = g.bytes_at(o, s)
    recs = [struct.unpack_from("<HHHBB", raw, i) for i in range(0, s, 8)]
    return w, h, era, mt, recs

for p in [r"F:\KF\XJZB\maps\(4)Blood Bath.scm",
          r"F:\KF\XJZB\maps\BroodWar\WebMaps\(4)Crusader.scm"]:
    if not os.path.exists(p):
        print("MISSING", p); continue
    w, h, era, mt, recs = load(p)
    ts = TILESETS[era]
    dd = open(os.path.join(D, ts + ".dddata.bin"), "rb").read()
    print("#"*15, os.path.basename(p), ts, f"{w}x{h}", "recs", len(recs))
    def grp(cx, cy): return mt[cy*w+cx] >> 4
    for (eid, xc, yc, own, dis) in recs:
        req = struct.unpack_from("<256H", dd, eid*512)
        best = None
        for stride in (1,2,3,4,5,6,8):
            for tw in range(1, 9):
                th = (max(i for i,v in enumerate(req) if v) + 1)//tw if any(req) else 0
                if th < 1 or tw*th > 256: continue
                for even in (0,1):
                    lx = (xc - 16*tw)//32 + (0 if even else 0)
                    ty = (yc - 16*th)//32
                    ok = tot = 0
                    for y in range(th):
                        for x in range(tw):
                            cx, cy = lx+x, ty+y
                            if 0 <= cx < w and 0 <= cy < h:
                                tot += 1
                                if req[y*tw+x] == 0 or (req[y*tw+x]>>4) == grp(cx,cy): ok += 1
                    if tot and (best is None or ok/tot > best[0]):
                        best = (ok/tot, tw, th, ok, tot)
        print(f"  id={eid} xc={xc} yc={yc} nonzero_req={sum(1 for v in req if v)} best_match={best}")

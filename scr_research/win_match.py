import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm
D = r"F:\KF\XJZB\scr_research\tileset"
p = r"F:\KF\XJZB\maps\(4)Blood Bath.scm"
chk, gaps = pm.read_chk(p); g, sec = pm.parse_chk(chk, gaps)
o, s = sec[b"DIM "]; d = g.bytes_at(o, s); w = d[0]|d[1]<<8; h = d[2]|d[3]<<8
o, s = sec[b"MTXM"]; mt = struct.unpack_from("<%dH" % (s//2), g.bytes_at(o, s), 0)
dd = open(os.path.join(D, "platform.dddata.bin"), "rb").read()
print("map", w, h)
for (eid, xc, yc, own, dis) in [(256,1408,912,0,0),(257,1408,1232,0,0),(257,832,880,0,0),(256,768,1232,0,0)]:
    req = list(struct.unpack_from("<256H", dd, eid*512))
    lastnz = max(i for i,v in enumerate(req) if v)
    print(f"\n== id {eid} at ({xc},{yc}) tile({xc//32},{yc//32}) lastnz={lastnz}")
    # try strides: find w such that pattern repeats
    for tw in range(1, 13):
        for ty in range(1, 13):
            if tw*ty-1 != lastnz: continue
            lx = (xc - 16*tw)//32; ly = (yc - 16*ty)//32
            win = [mt[(ly+y)*w + (lx+x)] for y in range(ty) for x in range(tw)]
            match = sum(1 for a,b in zip(req[:tw*ty], win) if a == b)
            zeromatch = sum(1 for a,b in zip(req[:tw*ty], win) if a == 0)
            if match >= tw*ty*0.8 or match > 0:
                print(f"   tw={tw} ty={ty} pos=({lx},{ly}) exact={match}/{tw*ty}  req0s={zeromatch}")

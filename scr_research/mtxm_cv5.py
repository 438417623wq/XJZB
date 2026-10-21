import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm
D = r"F:\KF\XJZB\scr_research\tileset"
def load(p):
    chk, gaps = pm.read_chk(p); g, sec = pm.parse_chk(chk, gaps)
    o, s = sec[b"DIM "]; d = g.bytes_at(o, s); w = d[0]|d[1]<<8; h = d[2]|d[3]<<8
    o, s = sec[b"ERA "]; era = g.bytes_at(o, s)[0]
    o, s = sec[b"MTXM"]; mt = struct.unpack_from("<%dH" % (s//2), g.bytes_at(o, s), 0)
    return w, h, era, mt
TS = {0:"badlands",1:"platform",2:"install",3:"ashworld",4:"jungle",5:"desert",6:"ice",7:"twilight"}
for p in [r"F:\KF\XJZB\maps\(4)Blood Bath.scm", r"F:\KF\XJZB\maps\(4)Dark Crystal.scm",
          r"F:\KF\XJZB\maps\BroodWar\WebMaps\(4)Inferno.scm"]:
    if not os.path.exists(p): print("missing", p); continue
    w,h,era,mt = load(p)
    ts = TS[era]
    cv5 = open(os.path.join(D, ts+".cv5"),"rb").read()
    used = collections.Counter(g>>4 for g in mt)
    hist = collections.Counter()
    ex = {}
    for g_, c in used.items():
        if g_*52+2 > len(cv5): hist["OOR"] += c; continue
        v = struct.unpack_from("<H", cv5, g_*52)[0]
        hist[v] += c
        ex.setdefault(v, g_)
    print(f"### {os.path.basename(p)} {ts} groups_used={len(used)} max={max(used)}")
    print("   offset0 histogram over used groups:", dict(hist.most_common(8)))
    for v in (0,1,2,3):
        print(f"   offset0=={v}: example group {ex.get(v)}")

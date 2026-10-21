import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm
D = r"F:\KF\XJZB\scr_research\tileset"
TS = {0:"badlands",1:"platform",2:"install",3:"ashworld",4:"jungle",5:"desert",6:"ice",7:"twilight"}
def load(p):
    chk, gaps = pm.read_chk(p); g, sec = pm.parse_chk(chk, gaps)
    o, s = sec[b"DIM "]; d = g.bytes_at(o, s); w = d[0]|d[1]<<8; h = d[2]|d[3]<<8
    o, s = sec[b"ERA "]; era = g.bytes_at(o, s)[0]
    o, s = sec[b"MTXM"]; mt = struct.unpack_from("<%dH" % (s//2), g.bytes_at(o, s), 0)
    o, s = sec[b"DD2 "]; dd = [struct.unpack_from("<HHHBB", g.bytes_at(o, s), i) for i in range(0, s, 8)]
    tl = None
    if b"TILE" in sec:
        o, s = sec[b"TILE"]; tl = struct.unpack_from("<%dH" % (s//2), g.bytes_at(o, s), 0)
    return w, h, TS[era], mt, tl, dd

for p in [r"F:\KF\XJZB\maps\(4)Blood Bath.scm", r"F:\KF\XJZB\maps\(4)Dark Crystal.scm"]:
    w, h, ts, mt, tl, dd = load(p)
    cv5 = open(os.path.join(D, ts + ".cv5"), "rb").read()
    diff = [i for i in range(w*h) if tl is not None and mt[i] != tl[i]]
    print(f"### {os.path.basename(p)} {ts} {w}x{h} diff tiles (MTXM!=TILE) = {len(diff)}")
    print("   DD2 recs:", dd)
    # group the diff tiles into connected footprints
    ds = set(diff)
    seen = set(); comps = []
    for t in diff:
        if t in seen: continue
        stack = [t]; comp = []
        while stack:
            u = stack.pop()
            if u in seen: continue
            seen.add(u); comp.append(u)
            ux, uy = u % w, u // w
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx, ny = ux+dx, uy+dy
                if 0 <= nx < w and 0 <= ny < h:
                    v = ny*w+nx
                    if v in ds and v not in seen: stack.append(v)
        comps.append(comp)
    print(f"   connected footprints: {len(comps)}")
    for comp in comps[:8]:
        xs = [c % w for c in comp]; ys = [c // w for c in comp]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        tw, th = x1-x0+1, y1-y0+1
        # collect CV5 groups and ddData indices of the doodad groups
        ids = collections.Counter()
        for c in comp:
            t = mt[c]; grp = t >> 4
            if grp*52+20 <= len(cv5):
                f = struct.unpack_from("<10H", cv5, grp*52)
                ids[(f[0], f[6], f[7], f[8])] += 1
        print(f"     box ({x0},{y0})-({x1},{y1}) {tw}x{th} tiles={len(comp)} cv5 (idx,ddData,w,h)={dict(ids)}")
        # which DD2 record matches centre?
        cx, cy = (x0 + x1 + 1) * 16, (y0 + y1 + 1) * 16
        for r in dd:
            if abs(r[1]-cx) <= 16 and abs(r[2]-cy) <= 16:
                print(f"        DD2 id={r[0]} at ({r[1]},{r[2]}) -> centre guess ({cx},{cy})")

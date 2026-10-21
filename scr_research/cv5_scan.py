import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D = r"F:\KF\XJZB\scr_research\tileset"
for ts in ["badlands","jungle","install","twilight"]:
    b = open(os.path.join(D, ts + ".cv5"),"rb").read()
    n = len(b)//52
    cand = []
    for g in range(n):
        at = g*52
        u = struct.unpack_from("<10H", b, at)
        dd, w, h, u2 = u[6], u[7], u[8], u[9]
        if 0 < w <= 16 and 0 < h <= 16 and dd < 512:
            cand.append((g, u[0], u[1], u[2], u[3], u[4], u[5], dd, w, h, u2))
    print(f"=== {ts}: n={n} plausible-doodad records={len(cand)}")
    for c in cand[:15]:
        print(f"   g{c[0]:5d} index={c[1]:5d} flags=0x{c[2]:04x} ov={c[3]:5d} rem={c[4]:5d} name={c[5]:5d} unk={c[6]:3d} ddData={c[7]:4d} w={c[8]:2d} h={c[9]:2d} u2={c[10]}")

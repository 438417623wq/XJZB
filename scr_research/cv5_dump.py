import sys, os, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm, sc_archive
D = r"F:\KF\XJZB\scr_research\tileset"
p = r"F:\KF\XJZB\maps\(4)Blood Bath.scm"
chk, gaps = pm.read_chk(p); g, sec = pm.parse_chk(chk, gaps)
o, s = sec[b"MTXM"]; mt = struct.unpack_from("<%dH" % (s//2), g.bytes_at(o, s), 0)
o, s = sec[b"DIM "]; d = g.bytes_at(o, s); w = d[0]|d[1]<<8
cv5 = open(os.path.join(D, "platform.cv5"), "rb").read()
print("platform.cv5 len", len(cv5), "groups", len(cv5)//52)
# group used at tile (38,24) -> idx 24*64+38
for (x, y) in [(38,24),(44,28),(26,27),(32,32)]:
    t = mt[y*w+x]; grp = t >> 4
    rec = cv5[grp*52:(grp+1)*52]
    u = struct.unpack_from("<26H", rec)
    print(f"tile({x},{y}) MTXM={t} 0x{t:04x} group={grp} var={t&15}")
    print("   u16[0..9]:", u[:10])
    print("   u16[10..25]:", u[10:])
    print("   hex:", rec.hex(" "))

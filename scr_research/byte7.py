import sys, os, glob, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm
b7 = collections.Counter(); b6 = collections.Counter(); maps = 0; recs = 0
xmax = 0; ymax = 0
for p in sorted(glob.glob(r"F:\KF\XJZB\AndroidPort\assets_src\maps\*.chk")):
    try:
        chk, gaps = pm.read_chk(p)
        if not chk: continue
        g, sec = pm.parse_chk(chk, gaps)
        if b"DD2 " not in sec: continue
        maps += 1
        o, s = sec[b"DD2 "]; raw = g.bytes_at(o, s)
        for i in range(0, s, 8):
            _, x, y, ow, fl = struct.unpack_from("<HHHBB", raw, i)
            b7[fl] += 1; b6[ow] += 1; recs += 1
            xmax = max(xmax, x); ymax = max(ymax, y)
    except Exception as e:
        pass
print("maps with DD2:", maps, "records:", recs)
print("byte 7 (offset 7) value histogram:", dict(b7.most_common(12)))
print("byte 6 (owner) value histogram:", dict(b6.most_common(12)))
print("max x:", xmax, "max y:", ymax)

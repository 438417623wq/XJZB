import sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm
p = r"F:\KF\XJZB\maps\BroodWar\WebMaps\(4)Inferno.scm"
chk, gaps = pm.read_chk(p)
g, sec = pm.parse_chk(chk, gaps)
off, sz = sec[b"DD2 "]
raw = g.bytes_at(off, sz)
rel = [(a-off, s) for a, s in gaps if off <= a < off+sz]
print("DD2", off, sz, "gaps inside:", rel)
for shift in (0, 1, -1):
    d = raw[shift:] if shift >= 0 else b"\x00"*(-shift) + raw
    recs = [struct.unpack_from("<HHHBB", d, i) for i in range(0, (len(d)//8)*8, 8)]
    bad = sum(1 for r in recs if r[0] > 511 or r[1] > 6144 or r[2] > 6144)
    print(f"shift={shift:+d} recs={len(recs)} out-of-range={bad} first6={recs[:6]}")

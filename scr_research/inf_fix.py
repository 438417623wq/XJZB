import sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"F:\KF\XJZB\AndroidPort\tools")
import pipeline_maps as pm
p = r"F:\KF\XJZB\maps\BroodWar\WebMaps\(4)Inferno.scm"
chk, gaps = pm.read_chk(p)
g, sec = pm.parse_chk(chk, gaps)
off, sz = sec[b"DD2 "]
raw = bytearray(g.bytes_at(off, sz))
# hypothesis: the zero byte inserted at rel 73 is misplaced; remove it
d = raw[:73] + raw[74:] + b"\x00"
recs = [struct.unpack_from("<HHHBB", d, i) for i in range(0, (len(d)//8)*8, 8)]
bad = [(i,r) for i,r in enumerate(recs) if r[0] > 511 or r[1] > 6144 or r[2] > 6144]
print("after removing rel-73 zero: recs", len(recs), "out-of-range", len(bad), bad[:5])
print("recs 8..16:", recs[8:16])
print("all ids distinct:", sorted(set(r[0] for r in recs)))

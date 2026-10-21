import sys, os, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"F:\KF\XJZB\AndroidPort\assets_src\maps\(4)Inferno.chk"
b = open(p, "rb").read()
valid = set(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ ")
sec = {}; q = 0
while q + 8 <= len(b):
    tag = b[q:q+4]; size = struct.unpack_from("<I", b, q+4)[0]
    if not all(c in valid for c in tag) or q+8+size > len(b):
        q += 1; continue
    sec.setdefault(tag, []).append((q+8, size)); q += 8 + size
print("tags:", sorted(t.decode() for t in sec))
for t in (b"VER ", b"ERA ", b"IVE2", b"DD2 "):
    if t in sec: print(t, [ (o,s) for o,s in sec[t] ], "size", sec[t][0][1])
o, s = sec[b"DD2 "][0]
print("DD2 bytes", s, "recs", s//8)
recs = [struct.unpack_from("<HHHBB", b, o+i) for i in range(0, s, 8)]
bad = [(i, r) for i, r in enumerate(recs) if r[0] > 511]
print("ids>511 count:", len(bad))
print("first bad:", bad[:5])
print("first 24 recs:", recs[:24])
print("last 8 recs:", recs[-8:])

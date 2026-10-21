import sys, os, glob, struct, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
valid = set(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ ")
def sections(b):
    sec = {}; q = 0
    while q + 8 <= len(b):
        tag = b[q:q+4]; size = struct.unpack_from("<I", b, q+4)[0]
        if not all(c in valid for c in tag) or q+8+size > len(b):
            q += 1; continue
        sec.setdefault(tag, []).append((q+8, size)); q += 8 + size
    return sec
b7 = collections.Counter(); b6 = collections.Counter(); maps = 0; recs = 0
xmax = ymax = 0
for p in sorted(glob.glob(r"F:\KF\XJZB\AndroidPort\assets_src\maps\*.chk")):
    b = open(p, "rb").read()
    sec = sections(b)
    if b"DD2 " not in sec: continue
    maps += 1
    o, s = sec[b"DD2 "][0]
    for i in range(0, s - 7, 8):
        _, x, y, ow, fl = struct.unpack_from("<HHHBB", b, o + i)
        b7[fl] += 1; b6[ow] += 1; recs += 1
        xmax = max(xmax, x); ymax = max(ymax, y)
print("maps with DD2:", maps, "records:", recs)
print("byte7 histogram:", dict(b7.most_common(12)))
print("byte6 (owner) histogram:", dict(b6.most_common(12)))
print("max x:", xmax, "max y:", ymax)

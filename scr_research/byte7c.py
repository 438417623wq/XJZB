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
b7 = collections.Counter(); b6 = collections.Counter()
clean = 0; dirty = 0; idmax = 0; idbad = 0
maps_ok = 0
for p in sorted(glob.glob(r"F:\KF\XJZB\AndroidPort\assets_src\maps\*.chk")):
    b = open(p, "rb").read(); sec = sections(b)
    if b"DD2 " not in sec or b"DIM " not in sec: continue
    o, s = sec[b"DIM "][0]; w = b[o]|b[o+1]<<8; h = b[o+2]|b[o+3]<<8
    o, s = sec[b"DD2 "][0]
    maps_ok += 1
    for i in range(0, s - 7, 8):
        did, x, y, ow, fl = struct.unpack_from("<HHHBB", b, o + i)
        idmax = max(idmax, did)
        if did > 511: idbad += 1; continue
        if x < w*32 and y < h*32:
            clean += 1; b7[fl] += 1; b6[ow] += 1
        else:
            dirty += 1
print("maps:", maps_ok, "in-bounds records:", clean, "out-of-bounds:", dirty, "id>511:", idbad, "max id:", idmax)
print("byte7 (in-bounds only):", dict(b7.most_common(10)))
print("byte6 owner (in-bounds only):", dict(b6.most_common(12)))

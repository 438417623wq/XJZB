import os, sys
sys.path.insert(0, ".")
import pipeline_maps as pm

for src, mid, w in [("maps\\(4)Blood Bath.scm","bloodbath",64),
                    ("maps\\(2)The Small Divide.scm","divide",64)]:
    r = pm.read_chk(os.path.join(pm.ROOT, src))
    chk, gaps = r
    g, sec = pm.parse_chk(chk, gaps)
    off, size = sec[b"DD2 "]
    raw = g.bytes_at(off, size)
    print(f"=== {mid} size={size} w={w} (map px = {w*32}) ===")
    for i in range(0, min(size, 96), 8):
        b = raw[i:i+8]
        u16 = [b[j] | (b[j+1]<<8) for j in (0,2,4)]
        print(f"  rec{i//8:3d} {' '.join('%02x'%c for c in b)}  u16={u16}  u8={list(b[6:8])}")

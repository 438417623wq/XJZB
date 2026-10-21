import sys, os, glob, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
def chk_sections(b):
    i = 0
    while i + 8 <= len(b):
        tag = b[i:i+4]
        size = struct.unpack_from("<I", b, i+4)[0]
        if i+8+size > len(b): break
        yield tag, i+8, size
        i += 8 + size
roots = [r"F:\KF\XJZB\maps", r"F:\KF\XJZB\AndroidPort\assets_src\maps", r"F:\KF\XJZB"]
seen = set()
rows = []
for root in roots:
    for p in glob.glob(os.path.join(root, "**", "*.chk"), recursive=True) + glob.glob(os.path.join(root, "**", "*.scm"), recursive=True) + glob.glob(os.path.join(root, "**", "*.scx"), recursive=True):
        rp = os.path.realpath(p)
        if rp in seen: continue
        seen.add(rp)
        b = open(p, "rb").read()
        if b[:4] == b"MPQ\x1a": continue
        sec = {}
        for tag, off, size in chk_sections(b):
            sec.setdefault(tag, (off, size))
        if b"DD2 " not in sec: continue
        era = struct.unpack_from("<H", b, sec[b"ERA "][0])[0] if b"ERA " in sec else None
        dim = struct.unpack_from("<HH", b, sec[b"DIM "][0]) if b"DIM " in sec else (None,None)
        off, size = sec[b"DD2 "]
        ids = [struct.unpack_from("<H", b, off+k)[0] for k in range(0, size-7, 8)]
        rows.append((os.path.basename(p), era, dim[0], dim[1], size//8, len(set(ids)), min(ids) if ids else None, max(ids) if ids else None, sorted(set(ids))))
TILESET = {0:"badlands",1:"platform",2:"install",3:"ashworld",4:"jungle",5:"desert",6:"ice",7:"twilight"}
print(f"{'map':40s} {'ts':9s} {'w x h':9s} {'n':>4s} {'dist':>4s} {'min':>4s} {'max':>4s}")
for r in sorted(rows, key=lambda x:(x[1] if x[1] is not None else 99, -x[4])):
    print(f"{r[0][:40]:40s} {TILESET.get(r[1],str(r[1])):9s} {str(r[2])+'x'+str(r[3]):9s} {r[4]:4d} {r[5]:4d} {str(r[6]):>4s} {str(r[7]):>4s}")
print()
print("=== ashworld maps: full id lists ===")
for r in rows:
    if r[1] == 3:
        print(f"{r[0]}: n={r[4]} dist={r[5]} ids={r[8]}")

import os, struct, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
root = r"F:\KF\XJZB"
hits = []
for dirpath, dirnames, filenames in os.walk(root):
    if 'scr_research' in dirpath: continue
    for fn in filenames:
        p = os.path.join(dirpath, fn)
        try:
            if os.path.getsize(p) > 40_000_000: continue
            d = open(p,'rb').read()
        except Exception: continue
        for tag in (b'DD2 ', b'DDDATA', b'IVE2', b'MBRF', b'SWNM'):
            if tag in d:
                hits.append((os.path.relpath(p,root), tag.decode('latin1'), d.count(tag)))
seen = {}
for rel, tag, c in hits:
    seen.setdefault(rel, []).append(f"{tag}x{c}")
for rel, tags in sorted(seen.items()):
    print(f"{rel}  ->  {', '.join(tags)}")
print("total files with any hit:", len(seen))

import sys, os, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
targets = [b"DDDATA", b"DDATA", b"DD2 ", b"DDOA"]
hits = {t: [] for t in targets}
n = 0
for root, dirs, files in os.walk(r"F:\KF\XJZB"):
    if "scr_research" in root: continue
    for f in files:
        p = os.path.join(root, f)
        try:
            if os.path.getsize(p) > 200*1024*1024: continue
            b = open(p, "rb").read()
        except Exception:
            continue
        n += 1
        for t in targets:
            c = b.count(t)
            if c: hits[t].append((p, c))
print("files scanned:", n)
for t in targets:
    print(f"\n=== {t!r}: {len(hits[t])} files")
    for p, c in hits[t][:12]:
        print(f"   {c:5d}  {p}")

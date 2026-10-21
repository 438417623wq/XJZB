import sys, re, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
print("=== literal b'DD2 ' occurrence counts in executables ===")
for p in [r"F:\KF\XJZB\StarEdit.exe", r"F:\KF\XJZB\StarCraft.exe", r"F:\KF\XJZB\Brood.exe"]:
    if not os.path.exists(p): print("  MISSING", p); continue
    b = open(p,"rb").read()
    print(f"  {os.path.basename(p):16s} size={len(b):9d}  b'DD2 '={b.count(b'DD2 ')}  b'DDATA'={b.count(b'DDATA')}  b'MTXM'={b.count(b'MTXM')}  b'TILE'={b.count(b'TILE')}  b'THG2'={b.count(b'THG2')}  b'SWNM'={b.count(b'SWNM')}  b'MBRF'={b.count(b'MBRF')}  b'IVE2'={b.count(b'IVE2')}  b'CRGB'={b.count(b'CRGB')}  b'STRx'={b.count(b'STRx')}")
print()
print("=== context around each b'DD2 ' hit in StarEdit.exe ===")
b = open(r"F:\KF\XJZB\StarEdit.exe","rb").read()
for m in re.finditer(rb"DD2 ", b):
    o = m.start()
    ctx = b[max(0,o-48):o+48]
    print(f"  off {o:7d}: {ctx!r}")

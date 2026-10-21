import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
T = r"F:\KF\XJZB\AndroidPort\tools"
lines = open(os.path.join(T,"images_tbl2.txt"), encoding="utf-8", errors="replace").read().splitlines()
m = {}
for l in lines:
    a,b = l.split("\t",1)
    m[int(a)] = b
print("images.tbl small indices used by the enum first numbers:")
for i in (1,2,3,4,5,6,7,9,11,12,13):
    print(f"  {i:3d} {m.get(i)}")
print()
print("=== images.tbl 0..20 ===")
for i in range(0,21): print(f"  {i:3d} {m.get(i)}")

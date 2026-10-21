import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
T = r"F:\KF\XJZB\AndroidPort\tools"
lines = open(os.path.join(T,"images_tbl2.txt"), encoding="utf-8", errors="replace").read().splitlines()
print("=== images.tbl 552..722 ===")
for l in lines:
    idx = int(l.split("\t")[0])
    if 552 <= idx <= 722:
        print("  ", l)
print()
print("=== doodads PNG dir ===")
pngs = sorted(os.listdir(r"F:\KF\XJZB\AndroidPort\extracted\expand\doodads"))
print(len(pngs))
print(pngs)

import sys, os, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ps = glob.glob(r"F:\KF\XJZB\AndroidPort\assets_src\maps\**\*.chk", recursive=True)
print("chk found:", len(ps))
print(ps[:5])
if ps:
    b = open(ps[0],"rb").read()
    print("first 64 bytes:", b[:64])
    print("len", len(b), "DD2  at", b.find(b"DD2 "))

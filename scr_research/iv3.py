import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
t = open(r"F:\KF\XJZB\scr_research\staredit_chk.txt", encoding="utf-8", errors="replace").read().splitlines()
def show(a,b,label):
    print("#"*25, label)
    for i in range(a-1, min(b, len(t))):
        s = t[i].strip()
        if s: print(f"{i+1}| {s[:200]}")
show(194, 268, "VER / IVER / IVE2 block")
show(1002, 1020, "MBRF")
show(1152, 1162, "SWNM")

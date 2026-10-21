import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
t = open(r"F:\KF\XJZB\scr_research\staredit_chk.txt", encoding="utf-8", errors="replace").read().splitlines()
for tag in ["IVE2", "MBRF", "SWNM", "IVER"]:
    print("="*20, tag)
    for i,l in enumerate(t):
        if tag in l:
            print(f"--- line {i+1}: {l.strip()[:120]}")

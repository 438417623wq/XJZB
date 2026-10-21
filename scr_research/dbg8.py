import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"F:\KF\XJZB\scr_research\staredit_chk.txt"
lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
for key in ["IVE2", "MBRF", "SWNM", "IVER"]:
    print("#"*20, key)
    for i, l in enumerate(lines):
        if key in l:
            print(f"  line {i+1}: {l.strip()[:200]}")
    print()

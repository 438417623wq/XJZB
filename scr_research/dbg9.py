import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"F:\KF\XJZB\scr_research\staredit_chk.txt"
lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
for key in ["Remastered", "1.18", "1.16", "SWNM"]:
    print("#"*15, key)
    for i, l in enumerate(lines):
        if key.lower() in l.lower():
            print(f"  {i+1}: {l.strip()[:220]}")
    print()
print("=== SWNM body 1150-1165 ===")
for i in range(1149, 1166):
    print(f"{i+1}: {lines[i]}")

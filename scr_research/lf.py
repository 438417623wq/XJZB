import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
for p in [r"F:\KF\XJZB\AndroidPort\tools\listfile_BrooDat.txt"]:
    lines = open(p, encoding="latin1").read().splitlines()
    print(p, "lines:", len(lines))
    for pat in ("dddata", "cv5", "thingy"):
        hits = [l for l in lines if pat in l.lower()]
        print(f"  '{pat}': {len(hits)}")
        for h in hits[:8]: print("     ", h)

import sys, json, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"F:\KF\XJZB\scr_research\tree_Chkdraft.json"
if not os.path.exists(p):
    import glob
    c = glob.glob(r"F:\KF\XJZB\scr_research\tree_Chkdraft*.json") + glob.glob(r"F:\KF\XJZB\scr_research\*hkdraft*.json")
    print("candidates:", c); p = c[0] if c else None
if p:
    t = json.load(open(p, encoding="utf-8"))
    paths = [e["path"] for e in t.get("tree", [])]
    for pat in ("chk.h","chk.cpp","sc.h","sc.cpp","chkd_sc","chkd_scenario","mapping_core"):
        hits = [x for x in paths if pat in x]
        print(f"  '{pat}': {hits[:8]}")

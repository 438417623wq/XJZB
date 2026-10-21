import sys, json, os, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"F:\KF\XJZB\scr_research\tree_Chkdraft.json"
t = json.load(open(p, encoding="utf-8"))
paths = [e["path"] for e in t.get("tree", [])]
print("total entries:", len(paths), "truncated:", t.get("truncated"))
print()
print("=== scenario-related paths ===")
for x in paths:
    if "scenario" in x.lower(): print("  ", x)
print()
print("=== src/mapping_core top-level ===")
for x in sorted(paths):
    if x.startswith("src/mapping_core/") and x.count("/") == 2: print("  ", x)
print()
print("=== local Chkdraft files on disk ===")
for f in glob.glob(r"F:\KF\XJZB\scr_research\**\*hkd*", recursive=True)[:20]: print("  ", f)
for f in glob.glob(r"F:\KF\XJZB\scr_research\**\*.cpp", recursive=True)[:20]: print("  ", f)
for f in glob.glob(r"F:\KF\XJZB\scr_research\**\*.h", recursive=True)[:20]: print("  ", f)

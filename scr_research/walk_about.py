import json,sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
j=json.load(open(r"F:\KF\XJZB\scr_research\splash_doodadwalk.json",encoding="utf-8"))
print(j["_about"])

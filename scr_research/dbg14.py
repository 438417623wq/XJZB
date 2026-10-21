import sys, os, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
txt = open(r"F:\KF\XJZB\scr_research\bwenums.h", encoding="utf-8", errors="replace").read()
i = txt.find("enum struct SpriteTypes")
j = txt.find("};", i)
body = txt[i:j]
names = re.findall(r"^\s*(SPRITEID_\w+),?\s*$", body, re.M)
print("total SpriteTypes entries:", len(names))
for k, nm in enumerate(names[:135]):
    print(f"  {k:3d} {nm}")

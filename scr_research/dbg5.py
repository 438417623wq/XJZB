import sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"F:\KF\XJZB\scr_research\bwenums.h"
txt = open(p, encoding="utf-8", errors="replace").read()
i = txt.find("SpriteTypes")
print(txt[i-200:i+600])
print("....")
j = txt.find("SPRITEID_Scourge")
print(txt[j-1400:j+200])

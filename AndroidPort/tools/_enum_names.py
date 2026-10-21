import re
txt = open("_bwenums.h", encoding="utf8").read()
print("len", len(txt))
for m in re.finditer(r"enum\s+(\w+)\s*\{", txt):
    print(" enum", m.group(1), "at", m.start())

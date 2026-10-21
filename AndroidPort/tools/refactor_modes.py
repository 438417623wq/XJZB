"""One-shot refactor: fold the verbose mode-reset clusters in GameView into
a single clearTargetingModes() call, so the five v2.14 spell modes can be
added without growing every reset site by five lines."""
import re

P = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\GameView.java"
src = open(P, encoding="utf8").read()
lines = src.split("\n")

out = []
i = 0
replaced = 0
while i < len(lines):
    m = re.match(r"^(\s+)(\w+Mode) = false;$", lines[i])
    if m:
        # count the run of consecutive "<X>Mode = false;" lines
        j = i
        while j < len(lines) and re.match(r"^\s+\w+Mode = false;$", lines[j]):
            j += 1
        if j - i >= 3:
            out.append(m.group(1) + "clearTargetingModes();")
            replaced += 1
            i = j
            continue
    out.append(lines[i])
    i += 1

open(P, "w", encoding="utf8").write("\n".join(out))
print("clusters replaced:", replaced)

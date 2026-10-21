import io
p = r"F:\KF\XJZB\AndroidPort\进展报告.md"
src = io.open(p, encoding="utf-8").read()
sec = io.open(r"F:\KF\XJZB\AndroidPort\tools\_sec239.md", encoding="utf-8").read()
if not src.endswith("\n"): src += "\n"
io.open(p, "w", encoding="utf-8", newline="\n").write(src + "\n" + sec)
print("appended")
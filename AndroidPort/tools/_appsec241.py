import io
p = r"F:\KF\XJZB\AndroidPort\进展报告.md"
src = io.open(p, encoding="utf-8").read()
sec = io.open(r"F:\KF\XJZB\AndroidPort\tools\_sec241.md", encoding="utf-8").read()
if not src.endswith("\n"): src += "\n"
src = src + "\n" + sec
# status block: 107 -> 108
src = src.replace("> **当前状态(v2.39)**:桌面验证台 **107 项断言全 PASS**",
                  "> **当前状态(v2.39)**:桌面验证台 **108 项断言全 PASS**")
src = src.replace("> 安卓 socket 壳 / 大厅 UI / 对局接线),并在过程中修掉四个真 bug\n> (见「八之三十六」起的各节)。",
                  "> 安卓 socket 壳 / 大厅 UI / 对局接线),并在过程中修掉四个真 bug\n> (见「八之三十六」起的各节);v2.40 把联机的真实语义(共控一方打 AI)\n> 钉成了断言与规格。")
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("v2.40 section + status updated")
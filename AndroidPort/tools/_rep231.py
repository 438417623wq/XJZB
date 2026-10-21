import io, re
path = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(path, encoding="utf-8").read()
start = src.index("    /**\n     * v2.31: two independent simulations, one hostile link.")
end = src.index("    /**\n     * v2.21: the four tester findings from the 2.20 build.")
body = io.open(r"F:\KF\XJZB\AndroidPort\tools\_v231body.java", encoding="utf-8").read()
src = src[:start] + body + src[end:]
io.open(path, "w", encoding="utf-8", newline="\n").write(src)
print("replaced v231Tests")
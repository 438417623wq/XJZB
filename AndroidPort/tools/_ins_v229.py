import io, sys
path = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(path, encoding="utf-8").read()
body = io.open(r"F:\KF\XJZB\AndroidPort\tools\_v229body.java", encoding="utf-8").read()
anchor = "    /**\n     * v2.21: the four tester findings from the 2.20 build."
assert src.count(anchor) == 1, src.count(anchor)
src = src.replace(anchor, body + anchor)
io.open(path, "w", encoding="utf-8", newline="\n").write(src)
print("inserted")
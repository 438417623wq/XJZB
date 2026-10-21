import io
path = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(path, encoding="utf-8").read()
body = io.open(r"F:\KF\XJZB\AndroidPort\tools\_v230body.java", encoding="utf-8").read()
anchor = "    /**\n     * v2.21: the four tester findings from the 2.20 build."
assert src.count(anchor) == 1
src = src.replace(anchor, body + anchor)
anchor2 = "        System.out.println(\"[v229]\");\n        v229Tests();\n"
assert src.count(anchor2) == 1
src = src.replace(anchor2, anchor2 + "\n        System.out.println(\"[v230]\");\n        v230Tests();\n")
io.open(path, "w", encoding="utf-8", newline="\n").write(src)
print("inserted")
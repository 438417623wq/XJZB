import io
path = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(path, encoding="utf-8").read()
body = io.open(r"F:\KF\XJZB\AndroidPort\tools\_v236body.java", encoding="utf-8").read()
anchor = "    /**\n     * v2.21: the four tester findings from the 2.20 build."
assert src.count(anchor) == 1
src = src.replace(anchor, body + anchor)
a2 = "        System.out.println(\"[v234]\");\n        v234Tests();\n"
assert src.count(a2) == 1
src = src.replace(a2, a2 + "\n        System.out.println(\"[v236]\");\n        v236Tests();\n")
io.open(path, "w", encoding="utf-8", newline="\n").write(src)
print("inserted")
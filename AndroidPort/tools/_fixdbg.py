import io
p = r"F:\KF\XJZB\AndroidPort\tools\_Dbg231.java"
src = io.open(p, encoding="utf-8").read()
src = src.replace('        GameDesktop.readManifestPublic();',
                  '        GameDesktop.readManifestPublic();\n        GameDesktop.readMapPublic("bloodbath");')
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("ok")
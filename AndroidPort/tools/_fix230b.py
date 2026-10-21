import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()
old = '''                && Lockstep.decode("") == null
'''
new = '''                && com.xjzb.rts.core.Lockstep.decode("") == null
'''
assert src.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("fixed")
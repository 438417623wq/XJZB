import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"F:\KF\XJZB\AndroidPort\assets_src\maps\(1)Enslavers01.chk"
b = open(p,"rb").read()
print("1150..1160:", b[1150:1162].hex(" "))
print("17530..17560:", b[17530:17560].hex(" "))
print("17530..17560 repr:", b[17530:17560])

import io
p = r"F:\KF\XJZB\AndroidPort\进展报告.md"
src = io.open(p, encoding="utf-8").read()
# v2.35 was written before v2.37 existed; correct the stale "still v2.34" note
# so the log does not contradict the sections after it.
old = '''### 产物

```
APK: 仍是 星际争霸RTS-v2.34.apk(本期纯 tools/,安卓侧零改动)
GameDesktop: 103 项断言全 PASS
TcpLockstep: PASS(连跑 4 次 diffTurns=0)
素材比对: 未变(无素材改动)
```
'''
new = '''### 产物

```
APK: 本期当时仍是 星际争霸RTS-v2.34.apk(纯 tools/,安卓侧零改动);
     后续 v2.37 把 net/ 壳落地后才重新出包
GameDesktop: 当时 103 项断言全 PASS
TcpLockstep: PASS(连跑 4 次 diffTurns=0)
素材比对: 未变(无素材改动)
```
'''
assert src.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("v2.35 note corrected")
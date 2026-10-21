import io
p = r"F:\KF\XJZB\AndroidPort\进展报告.md"
src = io.open(p, encoding="utf-8").read()
src = src.replace("# 星际争霸 → 安卓原生 RTS:重构技术报告(v2.36)",
                  "# 星际争霸 → 安卓原生 RTS:重构技术报告(v2.39)")
old = '''> **当前状态(v2.36)**:桌面验证台 **104 项断言全 PASS**,另有
> **真实 TCP 环回双机对拍** 1 项 PASS;APK 为
> `星际争霸RTS-v2.36.apk`(281.4 MB,versionCode 36)。
> 三族可玩、15 章战役、素材全来自原版 MPQ;
> v2.30–v2.35 落地了 **WiFi 本地对战** 的协议层(锁步核心 / 分帧 /
> 握手 / 发现 / 大厅 / 断线判负 / 真 TCP 对拍),
> 剩下的只是安卓侧 socket 壳与大厅 UI。'''
new = '''> **当前状态(v2.39)**:桌面验证台 **107 项断言全 PASS**,另有
> **真实 TCP 环回双机对拍** 1 项 PASS;APK 为
> `星际争霸RTS-v2.39.apk`(281.4 MB,versionCode 39)。
> 三族可玩、15 章战役、素材全来自原版 MPQ;
> v2.30–v2.39 把 **WiFi 本地对战** 从协议层一路做到可玩的
> 大厅 + 对局(锁步核心 / 分帧 / 握手 / 发现 / 大厅 / 断线判负 /
> 真 TCP 对拍 / 安卓 socket 壳 / 大厅 UI / 对局接线),
> 并在过程中修掉四个真 bug(见「八之三十六」起的各节)。'''
assert src.count(old) == 1
io.open(p, "w", encoding="utf-8", newline="\n").write(src.replace(old, new))
print("title + status block -> v2.39")
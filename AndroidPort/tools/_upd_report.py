import io
p = r"F:\KF\XJZB\AndroidPort\进展报告.md"
src = io.open(p, encoding="utf-8").read()

old_title = "# 星际争霸 → 安卓原生 RTS:重构技术报告(v2.8)\n"
new_title = "# 星际争霸 → 安卓原生 RTS:重构技术报告(v2.36)\n"
assert src.count(old_title) == 1
src = src.replace(old_title, new_title)

# A current-status block, because the prose below is a LOG: it records what
# each batch did and stops at v2.8, so reading only the top would understate
# where the project actually is. The log is kept as-is; this is the index.
anchor = "\n---\n\n## 一、结论速览\n"
assert src.count(anchor) == 1
block = """
> **当前状态(v2.36)**:桌面验证台 **104 项断言全 PASS**,另有
> **真实 TCP 环回双机对拍** 1 项 PASS;APK 为
> `星际争霸RTS-v2.36.apk`(281.4 MB,versionCode 36)。
> 三族可玩、15 章战役、素材全来自原版 MPQ;
> v2.30–v2.35 落地了 **WiFi 本地对战** 的协议层(锁步核心 / 分帧 /
> 握手 / 发现 / 大厅 / 断线判负 / 真 TCP 对拍),
> 剩下的只是安卓侧 socket 壳与大厅 UI。
> 下面「一、结论速览」及之后各节是**当时的记录**,行号与数字停留在
> 各自那一版,最新进度看文末的「八之三十X」各节。

"""
src = src.replace(anchor, block + anchor)
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("title + status block updated")
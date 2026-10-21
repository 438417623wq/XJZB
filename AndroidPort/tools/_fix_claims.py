import io
p = r"F:\KF\XJZB\AndroidPort\进展报告.md"
src = io.open(p, encoding="utf-8").read()

# The status block must state exactly what the LAN match IS.
old = '''> v2.30–v2.39 把 **WiFi 本地对战** 从协议层一路做到可玩的
> 大厅 + 对局(锁步核心 / 分帧 / 握手 / 发现 / 大厅 / 断线判负 /
> 真 TCP 对拍 / 安卓 socket 壳 / 大厅 UI / 对局接线),
> 并在过程中修掉四个真 bug(见「八之三十六」起的各节)。'''
new = '''> v2.30–v2.39 把 **WiFi 本地对战** 从协议层一路做到可玩的大厅 + 对局
> (锁步核心 / 分帧 / 握手 / 发现 / 大厅 / 断线判负 / 真 TCP 对拍 /
> 安卓 socket 壳 / 大厅 UI / 对局接线),并在过程中修掉四个真 bug
> (见「八之三十六」起的各节)。
>
> **⚠ 当前联机的真实形态是"两台手机共控同一方,打 AI"**,不是 1v1。
> 原因:`Game` 的模型是"一个人类(team 0)+ 一个 AI(team 1)",
> 两台机器构建的是**同一张**棋盘,所以两边的命令都落在 team 0 上,
> 而 team 1 由各自的 AI 驱动。做真正的 1v1 需要**镜像队伍**
> (让第二台机器拥有 team 1、并关掉 AI),那是下一批的事,
> 详见「八之四十」。协议层与大厅层不受影响,全部已验证。'''
assert src.count(old) == 1
src = src.replace(old, new)

# v2.37's own section made the same over-claim.
old2 = '''### 未做(下一批)

- 观战;断线重连(判负已有,重连没有);
- 3 人以上对局(锁步的规范顺序本来就是 N 人的,但只有 2 人经过实测)。'''
new2 = '''### 未做(下一批)

- **真正的 1v1**:见「八之四十」——本期两台机器共控 team 0,
  打的是 AI,不是对方;
- 观战;断线重连(判负已有,重连没有);
- 3 人以上对局(锁步的规范顺序本来就是 N 人的,但只有 2 人经过实测)。'''
assert src.count(old2) == 1
src = src.replace(old2, new2)
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("claims corrected")
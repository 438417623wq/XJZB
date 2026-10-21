import io
p = r"F:\KF\XJZB\AndroidPort\进展报告.md"
src = io.open(p, encoding="utf-8").read()

old = '''### 未做(下一批)

- 大厅 **UI**(主机/加入/准备/开始)与 `GameView` 的联机接线;
- 观战;重连。

### 产物
'''
new = '''### 大厅 UI 与对局接线(同批落地)

- `LobbyActivity`:开房 / 搜索附近的房 / 加入 / 开始。屏幕是**派生**的
  (任何状态变化后 `refresh()` 一次),所以座位表、开始按钮的可用性、
  错误提示不会各说各话;
- 主机每秒重播一次信标(晚到的客机也能看到房间);
- `NetSession`:Socket 进不了 `Intent`,所以大厅把连好的链路放进这个
  单槽静态,对局 Activity 取走。**单槽是刻意的**——一台手机同时只打
  一局,单槽就不会把第二局串进来;离线启动时全为 null,老路径一个
  空判断都不加在热路径上;
- `GameView`:有 session 时,游戏循环改走**锁步三相位**
  (`receiveFrame` → `sendFrame` → `stepFrame`),这正是桌面
  `TcpLockstep` 验证过的形状;没有 session 时仍是一句 `game.update(dt)`;
- **联机对局禁用"重新开始"**:重开会新建一个 `Game`,而 peer 还指着
  旧的那个,两边会**悄悄各走各的**;现在直接提示"联机对战不能重新开始";
- `BuildConfig` 打开:`versionName` 只在这一个地方定义,握手要的版本
  字符串从它读,不会出现两份拷贝漂移(漂移 = 拒绝一个好端端的对手);
- `MainActivity` 加"局域网对战"按钮(不是第四个页签——大厅有自己的
  生命周期,页签一切换就拆掉它反而更糟)。

### 未做(下一批)

- 观战;断线重连(判负已有,重连没有);
- 3 人以上对局(锁步的规范顺序本来就是 N 人的,但只有 2 人经过实测)。

### 产物
'''
assert src.count(old) == 1
src = src.replace(old, new)

old2 = '''GameDesktop: 105 项断言全 PASS(新增 [v237] 5 子断言,连跑四次稳定)
TcpLockstep: PASS(diffTurns=0)
HudPreview: 全分辨率刷新通过
素材比对: same=6026 diff=0 only_apk=0 only_disk=0  GATE: PASS
```
'''
new2 = '''     新增 LobbyActivity(已在 APK manifest 中注册并核对)
GameDesktop: 105 项断言全 PASS(新增 [v237] 5 子断言,连跑四次稳定)
TcpLockstep: PASS(diffTurns=0)
HudPreview: 全分辨率刷新通过
素材比对: same=6026 diff=0 only_apk=0 only_disk=0  GATE: PASS
```
'''
assert src.count(old2) == 1
src = src.replace(old2, new2)
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("v2.37 section updated")
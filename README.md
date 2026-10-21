# 星际争霸 → 安卓原生 RTS（XJZB）

把 `F:\KF\XJZB` 里的《星际争霸：母巢之战》1.16.1 重构成**安卓原生游戏**：
纯 Java 游戏核心 + 自研 MPQ/GRP/CHK 逆向工具链，画面、地图、单位、音效全部来自原版数据。

- 包名：`com.xjzb.rts`　·　当前版本：**v2.44**（versionCode 44）　·　minSdk 21 / targetSdk 34
- 三族可玩、15 章战役、5 000+ 张地图、WiFi 局域网锁步对战
- 桌面验证台 **109 项断言全 PASS**，另有真实 TCP 环回双机对拍

---

## 目录结构

```
AndroidPort/
├── 进展报告.md                     全过程技术报告（v1 → v2.44，约 3500 行）
├── vX.Y方案-*.md                   各版本设计与落地方案
├── app/                            安卓 Gradle 工程
│   ├── app/src/main/java/com/xjzb/rts/
│   │   ├── MainActivity / GameActivity / GameView / LobbyActivity
│   │   └── core/                   Game（模拟+类型表+寻路+AI）/ SpriteBank / Lockstep
│   └── app/src/main/assets/        maps（5273 个文件）/ sprites / sounds / ui / missions
├── assets_src/                     素材管线中间产物（maps / sprites / palettes / manifest.json）
├── tools/                          逆向与验证工具链（Python + 桌面验证台）
│   ├── sc_archive.py               MPQ 读取（扇区表探测 + 缺口感知读取）
│   ├── mphuff.py / mpadi.py / pkware.py   压缩算法解码
│   ├── grp.py                      GRP 精灵解码
│   ├── pipeline_*.py               素材管线（sprites / sounds / ui / maps / portraits）
│   ├── GameDesktop.java            桌面验证台（JDK17 直接跑）
│   └── HudPreview.java             HUD 布局预览 + 重叠/出屏断言
├── maps/                           原版地图（.scm/.scx，从 MPQ 提取）
├── scr_research/                   CHK/DD2/doodad 格式考证资料
└── _evidence/                      像素级取证截图
```

## 构建

```powershell
cd AndroidPort\app
.\gradlew.bat assembleRelease      # 产物：app\build\outputs\apk\release\
```

依赖：JDK 17、Android SDK（`local.properties` 里的 `sdk.dir` 需指向本机 SDK）。
仓库走阿里云 Maven 镜像（见 `settings.gradle.kts`），因为 Google Maven 在部分网络下不可达。

## 本仓库不含什么

原版游戏数据与构建产物体积过大且受版权保护，**不入库**：

| 内容 | 原因 | 如何获得 |
| --- | --- | --- |
| `*.mpq` / `*.exe` / `*.dll` 等原版文件 | 版权数据，约 129 MB | 自备正版 1.16.1 拷贝放到仓库根目录 |
| `*.apk` | 单个 200–300 MB | 见 Release 附件 |
| `.gradle/`、`build/`、`tools/out/`、`tools/bin/` | 构建/工具链中间产物，可由脚本重新生成 | 跑 `tools/` 下对应 pipeline |

没有原版文件时，`tools/` 的提取脚本会失败，但 `assets/` 里已提交的成品素材足以直接构建 APK。

## 文档

- [进展报告](AndroidPort/进展报告.md) —— 每个版本的根因、修法、断言与真机复测清单
- [v2.44 方案](AndroidPort/v2.44方案-寻路瓦斯与对局美术修复.md) —— 最新一批（寻路碰撞体、瓦斯断链、敌方进攻、刺蛇死亡动画）
- [v2.43 方案](AndroidPort/v2.43方案-对局性能优化.md) —— 对局性能：相机快照、空间网格、寻路预算、16 ms 帧对齐

"""Append the v2.4 round to the progress report and bump the header."""
import io

P = r"F:\KF\XJZB\AndroidPort\进展报告.md"
s = io.open(P, encoding="utf-8").read()

s = s.replace("# 星际争霸 → 安卓原生 RTS:重构技术报告(v2.3)",
              "# 星际争霸 → 安卓原生 RTS:重构技术报告(v2.4)")

s = s.replace(
"""> v2.3 把**原版游戏内 UI(console)移植到手机端**:线框头像、命令卡、
> 官方单位名、金属面板,并按手机屏幕做适配。""",
"""> v2.3 把**原版游戏内 UI(console)移植到手机端**:线框头像、命令卡、
> 官方单位名、金属面板,并按手机屏幕做适配。
> v2.4 修掉一个**全局调色板红蓝通道反了**的底层素材 Bug,并落地五批
> 反馈/地图/战斗/UI/美化改进(落点标记、错误条、建造反馈、生产队列、
> 迷雾位图化、小地图重做、边缘卷动、暂停菜单、置灰角标、编队等)。""")

io.open(P, "w", encoding="utf-8").write(s)
print("header bumped")

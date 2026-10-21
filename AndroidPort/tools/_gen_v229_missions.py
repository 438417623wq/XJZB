"""v2.29 campaign generator: writes m06-m15 in the exact m01 style
(json.dumps indent=1, ensure_ascii=False) after validating every unit key
against Game.TYPES and every coordinate against the map's walk bitmap."""
import gzip, json, os, re, sys

ROOT = r"F:\KF\XJZB\AndroidPort"
ASSETS = os.path.join(ROOT, r"app\app\src\main\assets")
MISS = os.path.join(ASSETS, "missions")

# ---- the type table, scraped from Game.java so a typo cannot pass ----
TYPES = set()
for line in open(os.path.join(ASSETS, r"..\java\com\xjzb\rts\core\Game.java"), encoding="utf-8"):
    m = re.match(r'\s*t\("([a-z0-9_]+)"', line)
    if m: TYPES.add(m.group(1))
assert len(TYPES) > 80, len(TYPES)

def load(mid):
    meta = {}
    starts, units = [], []
    for line in open(os.path.join(ASSETS, "maps", mid, "meta.txt"), encoding="utf-8"):
        line = line.strip()
        if line.startswith("w="): meta["w"] = int(line[2:])
        elif line.startswith("h="): meta["h"] = int(line[2:])
        elif line.startswith("start="):
            p = line[6:].split(","); starts.append((int(p[0]), int(p[1])))
        elif line.startswith("unit="):
            p = line[5:].split(","); units.append((int(p[0]), float(p[1]), float(p[2])))
    raw = gzip.decompress(open(os.path.join(ASSETS, "maps", mid, "walk.bin.gz"), "rb").read())
    return meta["w"], meta["h"], raw, starts, units

def walk_at(raw, wm, x, y):
    return bool(raw[(int(y) // 8) * wm + (int(x) // 8)])

def snap(raw, wm, hm, x, y, maxr=12):
    """Nearest walkable minitile centre, in pixels. Mirrors Game.nearestPassMini,
    which is what the engine itself does for a deferred wave spawn -- a unit
    standing on a blocked minitile has no path and never moves."""
    if walk_at(raw, wm, x, y):
        return x, y
    mx, my = int(x) // 8, int(y) // 8
    for r in range(1, maxr + 1):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r: continue
                X, Y = mx + dx, my + dy
                if X < 0 or Y < 0 or X >= wm or Y >= hm: continue
                if raw[Y * wm + X]:
                    return X * 8 + 4, Y * 8 + 4
    return None

# ---- base builders (positions mirror the stock constructor's layout) ----
def zerg_base(sx, sy, extra=True):
    out = [("hatchery", sx, sy - 20, 0), ("over", sx + 90, sy + 60, 0)]
    for i in range(5):
        out.append(("drone", sx - 70 + i * 26, sy + 70, 0))
    if extra:
        out.append(("pool", sx + 150, sy + 20, 0))
    return out

def protoss_base(sx, sy):
    out = [("nexus", sx, sy - 20, 0), ("pylon", sx + 130, sy + 20, 0)]
    for i in range(5):
        out.append(("probe", sx - 70 + i * 26, sy + 70, 0))
    return out

def enemy_base(ex, ey, lings=4, hydras=2, sunkens=2, extra=()):
    out = [("hatchery", ex, ey - 20, 1), ("pool", ex - 150, ey + 60, 1)]
    for i in range(sunkens):
        out.append(("sunken", ex + 110 + i * 40, ey + 80, 1))
    for i in range(lings):
        out.append(("zergling", ex - 70 + i * 26, ey + 110, 1))
    for i in range(hydras):
        out.append(("hydra", ex + 40 + i * 30, ey + 130, 1))
    out.extend(extra)
    return out

def line(units):
    return [{"type": t, "x": x, "y": y, "team": tm} for (t, x, y, tm) in units]

def msg(t, text):
    return {"at": {"time": t}, "action": "message", "text": text}

def wave(t, units, frm, to, delay=0.5):
    return {"at": {"time": t}, "action": "wave", "units": units,
            "from": list(frm), "to": list(to), "delay": delay}

def reinf(t, units, frm, to, delay=0.4):
    return {"at": {"time": t}, "action": "reinforce", "units": units,
            "from": list(frm), "to": list(to), "delay": delay}

def lose(key, text):
    return {"at": {"lost": key}, "action": "lose", "text": text}

M = []   # (mission dict, home key for the lose event)

# =============================== ZERG CHAPTER ===============================
c0, c1 = (480, 336), (3616, 400)
M.append((dict(
 id="m06", name="第六关 · 虫群初醒", map="cyclone",
 playerRace="zerg", enemyRace="zerg", difficulty=0, economy=True,
 briefing=[
  "脑虫,你的孵化场在气旋平原上苏醒了。",
  "矿脉就在巢边,工蜂已经开始采集——但别指望慢慢憋出一支大军。",
  "对面只有一个巢穴,用你手上这支虫群直接碾过去。",
  "目标:歼灭对面的虫巢,保住自己的孵化场。"],
 startUnits=line(zerg_base(*c0) + [
  ("zergling", c0[0] - 20, c0[1] + 140, 0), ("zergling", c0[0] + 10, c0[1] + 140, 0),
  ("zergling", c0[0] + 40, c0[1] + 140, 0), ("zergling", c0[0] + 70, c0[1] + 140, 0),
  ("hydra", c0[0] + 130, c0[1] + 140, 0), ("hydra", c0[0] + 160, c0[1] + 140, 0)]
  + enemy_base(*c1, lings=4, hydras=2)),
 objectives=[{"kind": "destroyAll", "desc": "歼灭虫巢"},
             {"kind": "protect", "target": "hatchery", "desc": "孵化场不能被摧毁"}],
 events=[msg(60, "敌方虫群正在集结"),
         wave(90, ["zergling"] * 5, (c1[0] - 100, c1[1] + 200), c0, 0.4),
         reinf(150, ["zergling", "zergling", "hydra"], (c0[0] - 60, c0[1] + 240), c0),
         msg(200, "增援已抵达"),
         wave(240, ["zergling"] * 4 + ["hydra", "hydra"], (c1[0] - 60, c1[1] + 200), c0, 0.4),
         lose("hatchery", "孵化场被摧毁")],
 aiWaves=[["zergling", "zergling", "zergling", "hydra"],
          ["zergling", "hydra", "hydra", "zergling"],
          ["hydra", "hydra", "zergling", "zergling"]]), "hatchery"))

# m07: wasteland, lurker brood
w0, w1 = (2912, 304), (1344, 2800)
M.append((dict(
 id="m07", name="第七关 · 荒原猎场", map="wasteland",
 playerRace="zerg", enemyRace="zerg", difficulty=1, economy=True,
 briefing=[
  "荒原的沙尘里埋着另一支虫群的伏兵。",
  "它们把潜伏者埋进沙土,专等你把虫群挤成一团。",
  "提示:把部队拉开,别让潜伏者的穿刺一次扎穿整条战线。"],
 startUnits=line(zerg_base(*w0) + [
  ("zergling", w0[0] - 40, w0[1] + 140, 0), ("zergling", w0[0] - 10, w0[1] + 140, 0),
  ("zergling", w0[0] + 20, w0[1] + 140, 0), ("zergling", w0[0] + 50, w0[1] + 140, 0),
  ("zergling", w0[0] + 80, w0[1] + 140, 0), ("zergling", w0[0] + 110, w0[1] + 140, 0),
  ("hydra", w0[0] + 140, w0[1] + 140, 0), ("hydra", w0[0] + 170, w0[1] + 140, 0),
  ("hydra", w0[0] + 200, w0[1] + 140, 0), ("lurker", w0[0] + 230, w0[1] + 140, 0)]
  + enemy_base(*w1, lings=6, hydras=3, sunkens=3, extra=[
     ("lurker", w1[0] - 40, w1[1] + 150, 1), ("lurker", w1[0] + 10, w1[1] + 150, 1),
     ("hydraden", w1[0] + 200, w1[1] + 60, 1)])),
 objectives=[{"kind": "destroyAll", "desc": "清空荒原上的虫群"},
             {"kind": "protect", "target": "hatchery", "desc": "孵化场不能被摧毁"}],
 events=[msg(70, "侦测到潜伏者,注意队形"),
         wave(120, ["zergling"] * 6, (w1[0] - 80, w1[1] + 200), w0, 0.35),
         wave(260, ["lurker", "hydra", "hydra", "zergling", "zergling"],
              (w1[0] - 40, w1[1] + 200), w0, 0.45),
         reinf(300, ["hydra", "hydra", "lurker"], (w0[0] - 60, w0[1] + 240), w0),
         msg(420, "第二支虫群正在逼近"),
         wave(480, ["lurker", "lurker", "hydra", "hydra", "zergling"],
              (w1[0], w1[1] + 200), w0, 0.4),
         lose("hatchery", "孵化场被摧毁")],
 aiWaves=[["zergling", "zergling", "hydra"],
          ["zergling", "hydra", "lurker"],
          ["lurker", "hydra", "hydra", "zergling"]]), "hatchery"))

# m08: nightfall, survive against an air brood
n0, n1 = (1536, 272), (2688, 1680)
M.append((dict(
 id="m08", name="第八关 · 夜幕空袭", map="nightfall",
 playerRace="zerg", enemyRace="zerg", difficulty=1, economy=True,
 briefing=[
  "夜幕降临,北面的虫群把飞龙塔搬上了高地。",
  "这一战不必全歼对手——守住你的孵化场整整七分钟。",
  "提示:刺蛇是唯一能打空的现成单位,把它们留在巢边。"],
 startUnits=line(zerg_base(*n0) + [
  ("zergling", n0[0] - 60, n0[1] + 140, 0), ("zergling", n0[0] - 30, n0[1] + 140, 0),
  ("zergling", n0[0], n0[1] + 140, 0), ("zergling", n0[0] + 30, n0[1] + 140, 0),
  ("hydra", n0[0] + 60, n0[1] + 140, 0), ("hydra", n0[0] + 90, n0[1] + 140, 0),
  ("hydra", n0[0] + 120, n0[1] + 140, 0), ("hydra", n0[0] + 150, n0[1] + 140, 0),
  ("sunken", n0[0] - 110, n0[1] + 60, 0), ("sunken", n0[0] + 110, n0[1] + 60, 0),
  ("spore", n0[0] + 150, n0[1] - 40, 0)]
  + enemy_base(*n1, lings=4, hydras=3, sunkens=2, extra=[
     ("spire", n1[0] + 200, n1[1] + 40, 1), ("muta", n1[0] + 150, n1[1] + 160, 1),
     ("muta", n1[0] + 180, n1[1] + 160, 1)])),
 objectives=[{"kind": "survive", "time": 420, "desc": "守住孵化场 7 分钟"},
             {"kind": "protect", "target": "hatchery", "desc": "孵化场不能被摧毁"}],
 events=[msg(60, "敌方飞龙塔已完工"),
         wave(120, ["muta", "muta", "zergling", "zergling"], (n1[0] - 60, n1[1] + 200), n0, 0.5),
         msg(210, "第二波空袭进入航线"),
         wave(240, ["muta", "muta", "muta", "hydra"], (n1[0] - 30, n1[1] + 200), n0, 0.5),
         reinf(270, ["hydra", "hydra", "hydra"], (n0[0] - 60, n0[1] + 240), n0),
         msg(360, "最后一波:守护者也出动了"),
         wave(390, ["guardian", "muta", "muta", "hydra", "zergling", "zergling"],
              (n1[0], n1[1] + 200), n0, 0.45),
         lose("hatchery", "孵化场被摧毁")],
 aiWaves=[["zergling", "zergling", "hydra"],
          ["muta", "muta", "zergling"],
          ["muta", "guardian", "hydra", "zergling"]]), "hatchery"))

# m09: bonecanyon, ultralisk brood + player reinforcement
b0, b1 = (1632, 272), (2944, 3792)
M.append((dict(
 id="m09", name="第九关 · 白骨峡谷", map="bonecanyon",
 playerRace="zerg", enemyRace="zerg", difficulty=2, economy=True,
 briefing=[
  "白骨峡谷的虫群把雷兽洞穴挖进了岩壁。",
  "雷兽皮糙肉厚,靠小狗硬碰只会被碾碎——先用刺蛇磨,再让潜伏者收尾。",
  "中途会有增援从你身后抵达。"],
 startUnits=line(zerg_base(*b0) + [
  ("zergling", b0[0] - 90, b0[1] + 140, 0), ("zergling", b0[0] - 60, b0[1] + 140, 0),
  ("zergling", b0[0] - 30, b0[1] + 140, 0), ("zergling", b0[0], b0[1] + 140, 0),
  ("zergling", b0[0] + 30, b0[1] + 140, 0), ("zergling", b0[0] + 60, b0[1] + 140, 0),
  ("hydra", b0[0] + 90, b0[1] + 140, 0), ("hydra", b0[0] + 120, b0[1] + 140, 0),
  ("hydra", b0[0] + 150, b0[1] + 140, 0), ("hydra", b0[0] + 180, b0[1] + 140, 0),
  ("lurker", b0[0] + 210, b0[1] + 140, 0), ("lurker", b0[0] + 240, b0[1] + 140, 0)]
  + enemy_base(*b1, lings=6, hydras=4, sunkens=4, extra=[
     ("ucereb", b1[0] + 200, b1[1] + 40, 1), ("ultra", b1[0] + 150, b1[1] + 170, 1),
     ("ultra", b1[0] + 190, b1[1] + 170, 1), ("spore", b1[0] - 60, b1[1] + 80, 1)])),
 objectives=[{"kind": "destroyAll", "desc": "踏平白骨峡谷的虫巢"},
             {"kind": "protect", "target": "hatchery", "desc": "孵化场不能被摧毁"},
             {"kind": "protect", "target": "pool", "desc": "保住孵化池", "optional": True}],
 events=[msg(60, "雷兽的脚步声从峡谷深处传来"),
         wave(150, ["zergling"] * 8, (b1[0] - 80, b1[1] + 220), b0, 0.3),
         reinf(180, ["hydra", "hydra", "lurker"], (b0[0] - 60, b0[1] + 260), b0),
         msg(210, "增援已抵达"),
         wave(300, ["ultra", "hydra", "hydra", "zergling", "zergling"],
              (b1[0] - 40, b1[1] + 220), b0, 0.45),
         msg(450, "雷兽倾巢而出"),
         wave(480, ["ultra", "ultra", "ultra", "hydra", "hydra", "zergling", "zergling"],
              (b1[0], b1[1] + 220), b0, 0.4),
         lose("hatchery", "孵化场被摧毁")],
 aiWaves=[["zergling", "zergling", "hydra"],
          ["zergling", "hydra", "lurker"],
          ["ultra", "hydra", "hydra", "zergling"],
          ["ultra", "ultra", "hydra", "zergling", "zergling"]]), "hatchery"))

# m10: scorchedearth, defiler/queen brood, finale of the zerg chapter
s0, s1 = (2048, 272), (3744, 2064)
M.append((dict(
 id="m10", name="第十关 · 焦土决战", map="scorchedearth",
 playerRace="zerg", enemyRace="zerg", difficulty=2, economy=True,
 briefing=[
  "焦土。这里曾是人类的殖民点,现在只剩下一支占据要塞的虫群。",
  "污染者的瘟疫与皇后的寄生会一层层剥掉你的虫群。",
  "虫族战役的最后一战:把这座要塞从地图上抹掉。"],
 startUnits=line(zerg_base(*s0) + [
  ("zergling", s0[0] - 90, s0[1] + 140, 0), ("zergling", s0[0] - 60, s0[1] + 140, 0),
  ("zergling", s0[0] - 30, s0[1] + 140, 0), ("zergling", s0[0], s0[1] + 140, 0),
  ("zergling", s0[0] + 30, s0[1] + 140, 0), ("zergling", s0[0] + 60, s0[1] + 140, 0),
  ("zergling", s0[0] + 90, s0[1] + 140, 0), ("zergling", s0[0] + 120, s0[1] + 140, 0),
  ("hydra", s0[0] + 150, s0[1] + 140, 0), ("hydra", s0[0] + 180, s0[1] + 140, 0),
  ("hydra", s0[0] + 210, s0[1] + 140, 0), ("lurker", s0[0] + 240, s0[1] + 140, 0),
  ("lurker", s0[0] + 270, s0[1] + 140, 0), ("ultra", s0[0] + 300, s0[1] + 140, 0),
  ("sunken", s0[0] - 110, s0[1] + 60, 0), ("sunken", s0[0] + 110, s0[1] + 60, 0),
  ("spore", s0[0] - 150, s0[1] - 40, 0), ("spore", s0[0] + 150, s0[1] - 40, 0)]
  + enemy_base(*s1, lings=8, hydras=4, sunkens=4, extra=[
     ("hive", s1[0] + 220, s1[1] - 60, 1), ("mutapit", s1[0] + 220, s1[1] + 40, 1),
     ("greatspire", s1[0] + 220, s1[1] + 140, 1),
     ("defiler", s1[0] - 60, s1[1] + 170, 1), ("defiler", s1[0] - 20, s1[1] + 170, 1),
     ("queen", s1[0] + 30, s1[1] + 170, 1), ("queen", s1[0] + 70, s1[1] + 170, 1),
     ("guardian", s1[0] + 110, s1[1] + 170, 1), ("guardian", s1[0] + 150, s1[1] + 170, 1),
     ("devourer", s1[0] + 190, s1[1] + 170, 1), ("ultra", s1[0] + 230, s1[1] + 170, 1)])),
 objectives=[{"kind": "destroyAll", "desc": "抹平焦土要塞"},
             {"kind": "protect", "target": "hatchery", "desc": "孵化场不能被摧毁"}],
 events=[msg(60, "污染者的菌雾正在扩散"),
         wave(150, ["zergling"] * 8 + ["hydra", "hydra"], (s1[0] - 80, s1[1] + 240), s0, 0.3),
         reinf(200, ["hydra", "hydra", "lurker", "ultra"], (s0[0] - 60, s0[1] + 280), s0),
         msg(230, "增援已抵达"),
         wave(330, ["ultra", "ultra", "hydra", "hydra", "zergling", "zergling"],
              (s1[0] - 40, s1[1] + 240), s0, 0.4),
         msg(480, "虫群倾巢而出,守护者与吞噬者升空"),
         wave(510, ["guardian", "guardian", "devourer", "ultra", "ultra",
                    "hydra", "hydra", "zergling", "zergling", "zergling"],
              (s1[0], s1[1] + 240), s0, 0.35),
         lose("hatchery", "孵化场被摧毁")],
 aiWaves=[["zergling", "zergling", "hydra"],
          ["zergling", "hydra", "lurker"],
          ["ultra", "hydra", "hydra", "zergling"],
          ["guardian", "devourer", "ultra", "hydra", "zergling"]]), "hatchery"))

# ============================== PROTOSS CHAPTER =============================
p0, p1 = (704, 1488), (3360, 1488)
M.append((dict(
 id="m11", name="第十一关 · 圣所初战", map="sanctuary",
 playerRace="protoss", enemyRace="zerg", difficulty=0, economy=True,
 briefing=[
  "执行者,圣所的星灵枢纽已经落成。",
  "狂热者近身无敌,但别让他们单独冲进刺蛇的火网。",
  "龙骑士射程更远,让他们站在狂热者身后。"],
 startUnits=line(protoss_base(*p0) + [
  ("zealot", p0[0] - 60, p0[1] + 140, 0), ("zealot", p0[0] - 30, p0[1] + 140, 0),
  ("zealot", p0[0], p0[1] + 140, 0), ("zealot", p0[0] + 30, p0[1] + 140, 0),
  ("dragoon", p0[0] + 60, p0[1] + 140, 0), ("dragoon", p0[0] + 90, p0[1] + 140, 0)]
  + enemy_base(*p1, lings=4, hydras=2)),
 objectives=[{"kind": "destroyAll", "desc": "肃清圣所上的虫群"},
             {"kind": "protect", "target": "nexus", "desc": "星灵枢纽不能被摧毁"}],
 events=[msg(60, "虫群正在集结"),
         wave(90, ["zergling"] * 5, (p1[0] - 100, p1[1] + 200), p0, 0.4),
         reinf(150, ["zealot", "zealot", "dragoon"], (p0[0] - 60, p0[1] + 240), p0),
         msg(200, "增援已抵达"),
         wave(250, ["zergling"] * 4 + ["hydra", "hydra"], (p1[0] - 60, p1[1] + 200), p0, 0.4),
         lose("nexus", "星灵枢纽被摧毁")],
 aiWaves=[["zergling", "zergling", "zergling", "hydra"],
          ["zergling", "hydra", "hydra", "zergling"],
          ["hydra", "hydra", "zergling", "zergling"]]), "nexus"))

# m12: azureplains, survive vs lurker+air
a0, a1 = (3072, 240), (1024, 240)
M.append((dict(
 id="m12", name="第十二关 · 碧蓝防线", map="azureplains",
 playerRace="protoss", enemyRace="zerg", difficulty=1, economy=True,
 briefing=[
  "碧蓝平原的虫群正从西线压来。",
  "守住星灵枢纽八分钟。光子炮台是星灵唯一的静态火力。",
  "提示:机械核心能造出金甲虫,它的炮弹对成群的虫兵最有效。"],
 startUnits=line(protoss_base(*a0) + [
  ("zealot", a0[0] - 60, a0[1] + 140, 0), ("zealot", a0[0] - 30, a0[1] + 140, 0),
  ("zealot", a0[0], a0[1] + 140, 0), ("zealot", a0[0] + 30, a0[1] + 140, 0),
  ("dragoon", a0[0] + 60, a0[1] + 140, 0), ("dragoon", a0[0] + 90, a0[1] + 140, 0),
  ("dragoon", a0[0] + 120, a0[1] + 140, 0), ("dragoon", a0[0] + 150, a0[1] + 140, 0),
  ("photon", a0[0] - 110, a0[1] + 60, 0), ("photon", a0[0] + 110, a0[1] + 60, 0),
  ("reaver", a0[0] + 180, a0[1] + 140, 0)]
  + enemy_base(*a1, lings=6, hydras=4, sunkens=3, extra=[
     ("hydraden", a1[0] + 200, a1[1] + 40, 1), ("spire", a1[0] + 200, a1[1] + 120, 1),
     ("lurker", a1[0] - 40, a1[1] + 150, 1), ("muta", a1[0] + 120, a1[1] + 160, 1)])),
 objectives=[{"kind": "survive", "time": 480, "desc": "守住星灵枢纽 8 分钟"},
             {"kind": "protect", "target": "nexus", "desc": "星灵枢纽不能被摧毁"}],
 events=[msg(60, "东西两线的虫群同时开始推进"),
         wave(120, ["zergling"] * 6 + ["hydra"], (a1[0] - 80, a1[1] + 200), a0, 0.3),
         wave(210, ["muta", "muta", "zergling", "zergling"], (a1[0] - 40, a1[1] + 200), a0, 0.45),
         reinf(240, ["dragoon", "dragoon", "zealot", "zealot"], (a0[0] - 60, a0[1] + 240), a0),
         msg(300, "潜伏者钻出地面"),
         wave(330, ["lurker", "lurker", "hydra", "hydra"], (a1[0], a1[1] + 200), a0, 0.4),
         msg(420, "最后一波正在逼近"),
         wave(450, ["muta", "muta", "lurker", "hydra", "zergling", "zergling", "zergling"],
              (a1[0] - 20, a1[1] + 200), a0, 0.35),
         lose("nexus", "星灵枢纽被摧毁")],
 aiWaves=[["zergling", "zergling", "hydra"],
          ["zergling", "hydra", "lurker"],
          ["muta", "lurker", "hydra", "zergling"]]), "nexus"))

# m13: thinice, big map push
t0, t1 = (4480, 272), (5824, 2064)
M.append((dict(
 id="m13", name="第十三关 · 薄冰之上", map="thinice",
 playerRace="protoss", enemyRace="zerg", difficulty=1, economy=True,
 briefing=[
  "薄冰是一张开阔的大图,虫群在东南角经营了一座完整的巢穴。",
  "路程很长,增援会分批抵达——先集结,再推进。",
  "目标:全图歼灭。"],
 startUnits=line(protoss_base(*t0) + [
  ("zealot", t0[0] - 60, t0[1] + 140, 0), ("zealot", t0[0] - 30, t0[1] + 140, 0),
  ("zealot", t0[0], t0[1] + 140, 0), ("zealot", t0[0] + 30, t0[1] + 140, 0),
  ("dragoon", t0[0] + 60, t0[1] + 140, 0), ("dragoon", t0[0] + 90, t0[1] + 140, 0),
  ("scout", t0[0] + 120, t0[1] + 140, 0)]
  + enemy_base(*t1, lings=6, hydras=4, sunkens=4, extra=[
     ("spire", t1[0] + 200, t1[1] + 40, 1), ("hydraden", t1[0] - 220, t1[1] + 40, 1),
     ("muta", t1[0] + 120, t1[1] + 170, 1), ("muta", t1[0] + 160, t1[1] + 170, 1),
     ("lurker", t1[0] - 40, t1[1] + 170, 1)])),
 objectives=[{"kind": "destroyAll", "desc": "全图歼灭虫群"},
             {"kind": "protect", "target": "nexus", "desc": "星灵枢纽不能被摧毁"}],
 events=[msg(70, "侦察机回报:东南角有一座完整的虫巢"),
         wave(180, ["zergling"] * 6 + ["hydra", "hydra"], (t1[0] - 80, t1[1] + 220), t0, 0.3),
         reinf(240, ["dragoon", "dragoon", "zealot", "zealot"], (t0[0] - 60, t0[1] + 260), t0),
         msg(280, "第一支援军抵达"),
         wave(400, ["muta", "muta", "hydra", "hydra", "zergling", "zergling"],
              (t1[0] - 40, t1[1] + 220), t0, 0.4),
         reinf(480, ["reaver", "dragoon", "dragoon"], (t0[0] - 60, t0[1] + 260), t0),
         msg(520, "金甲虫已空运到位"),
         wave(600, ["muta", "muta", "muta", "lurker", "hydra", "zergling", "zergling"],
              (t1[0], t1[1] + 220), t0, 0.35),
         lose("nexus", "星灵枢纽被摧毁")],
 aiWaves=[["zergling", "zergling", "hydra"],
          ["zergling", "hydra", "lurker"],
          ["muta", "hydra", "hydra", "zergling"]]), "nexus"))

# m14: sirocco, heavy brood
r0, r1 = (3936, 880), (4192, 3120)
M.append((dict(
 id="m14", name="第十四关 · 热风攻坚", map="sirocco",
 playerRace="protoss", enemyRace="zerg", difficulty=2, economy=True,
 briefing=[
  "热风的虫群经营了一座带完整科技树的要塞。",
  "圣堂武士的心灵风暴能一次烧穿整片虫群,但他们的护盾很薄。",
  "目标:摧毁热风上的全部虫巢。"],
 startUnits=line(protoss_base(*r0) + [
  ("zealot", r0[0] - 60, r0[1] + 140, 0), ("zealot", r0[0] - 30, r0[1] + 140, 0),
  ("zealot", r0[0], r0[1] + 140, 0), ("zealot", r0[0] + 30, r0[1] + 140, 0),
  ("dragoon", r0[0] + 60, r0[1] + 140, 0), ("dragoon", r0[0] + 90, r0[1] + 140, 0),
  ("dragoon", r0[0] + 120, r0[1] + 140, 0), ("templar", r0[0] + 150, r0[1] + 140, 0),
  ("templar", r0[0] + 180, r0[1] + 140, 0), ("photon", r0[0] - 110, r0[1] + 60, 0),
  ("photon", r0[0] + 110, r0[1] + 60, 0)]
  + enemy_base(*r1, lings=8, hydras=5, sunkens=4, extra=[
     ("hive", r1[0] + 220, r1[1] - 60, 1), ("greatspire", r1[0] + 220, r1[1] + 40, 1),
     ("ucereb", r1[0] - 240, r1[1] - 60, 1), ("mutapit", r1[0] - 240, r1[1] + 40, 1),
     ("ultra", r1[0] + 120, r1[1] + 170, 1), ("ultra", r1[0] + 160, r1[1] + 170, 1),
     ("defiler", r1[0] - 40, r1[1] + 170, 1),
     ("guardian", r1[0] + 200, r1[1] + 170, 1),
     ("devourer", r1[0] - 80, r1[1] + 170, 1)])),
 objectives=[{"kind": "destroyAll", "desc": "摧毁热风上的全部虫巢"},
             {"kind": "protect", "target": "nexus", "desc": "星灵枢纽不能被摧毁"},
             {"kind": "protect", "target": "pylon", "desc": "保住水晶塔", "optional": True}],
 events=[msg(60, "污染者的菌雾正在逼近"),
         wave(150, ["zergling"] * 8 + ["hydra", "hydra"], (r1[0] - 80, r1[1] + 240), r0, 0.3),
         reinf(200, ["dragoon", "dragoon", "templar"], (r0[0] - 60, r0[1] + 280), r0),
         msg(240, "增援已抵达"),
         wave(330, ["ultra", "ultra", "hydra", "hydra", "zergling", "zergling"],
              (r1[0] - 40, r1[1] + 240), r0, 0.4),
         msg(480, "守护者与吞噬者升空"),
         wave(510, ["guardian", "guardian", "devourer", "ultra", "ultra",
                    "hydra", "hydra", "zergling", "zergling", "zergling"],
              (r1[0], r1[1] + 240), r0, 0.35),
         lose("nexus", "星灵枢纽被摧毁")],
 aiWaves=[["zergling", "zergling", "hydra"],
          ["zergling", "hydra", "lurker"],
          ["ultra", "hydra", "hydra", "zergling"],
          ["guardian", "devourer", "ultra", "hydra", "zergling"]]), "nexus"))

# m15: riverlethe, finale with two enemy bases
v0 = (3520, 240)
v1 = (3808, 3568)
v2 = (928, 5904)
M.append((dict(
 id="m15", name="第十五关 · 忘川毕业考", map="riverlethe",
 playerRace="protoss", enemyRace="zerg", difficulty=2, economy=True,
 briefing=[
  "忘川。南面的两条虫脉各有一座主巢,互为犄角。",
  "这是星灵战役的毕业考:三座基地、四个方向,没有捷径。",
  "提示:航空母舰和仲裁机可以走空路绕开地面防线。"],
 startUnits=line(protoss_base(*v0) + [
  ("zealot", v0[0] - 90, v0[1] + 140, 0), ("zealot", v0[0] - 60, v0[1] + 140, 0),
  ("zealot", v0[0] - 30, v0[1] + 140, 0), ("zealot", v0[0], v0[1] + 140, 0),
  ("zealot", v0[0] + 30, v0[1] + 140, 0), ("zealot", v0[0] + 60, v0[1] + 140, 0),
  ("dragoon", v0[0] + 90, v0[1] + 140, 0), ("dragoon", v0[0] + 120, v0[1] + 140, 0),
  ("dragoon", v0[0] + 150, v0[1] + 140, 0), ("templar", v0[0] + 180, v0[1] + 140, 0),
  ("templar", v0[0] + 210, v0[1] + 140, 0), ("reaver", v0[0] + 240, v0[1] + 140, 0),
  ("carrier", v0[0] + 270, v0[1] + 140, 0),
  ("photon", v0[0] - 110, v0[1] + 60, 0), ("photon", v0[0] + 110, v0[1] + 60, 0)]
  + enemy_base(*v1, lings=8, hydras=5, sunkens=4, extra=[
     ("hive", v1[0] + 220, v1[1] - 60, 1), ("greatspire", v1[0] + 220, v1[1] + 40, 1),
     ("mutapit", v1[0] - 240, v1[1] + 40, 1), ("ucereb", v1[0] - 240, v1[1] - 60, 1),
     ("ultra", v1[0] + 120, v1[1] + 170, 1), ("guardian", v1[0] + 160, v1[1] + 170, 1),
     ("devourer", v1[0] + 200, v1[1] + 170, 1), ("queen", v1[0] - 40, v1[1] + 170, 1)])
  + enemy_base(*v2, lings=6, hydras=4, sunkens=3, extra=[
     ("hydraden", v2[0] + 200, v2[1] + 40, 1), ("spire", v2[0] - 220, v2[1] + 40, 1),
     ("lurker", v2[0] + 120, v2[1] + 170, 1), ("muta", v2[0] - 40, v2[1] + 170, 1)])),
 objectives=[{"kind": "destroyAll", "desc": "歼灭忘川上的全部虫群"},
             {"kind": "protect", "target": "nexus", "desc": "星灵枢纽不能被摧毁"}],
 events=[msg(60, "两座主巢同时开始生产"),
         wave(150, ["zergling"] * 6 + ["hydra", "hydra"], (v1[0] - 80, v1[1] + 240), v0, 0.3),
         wave(210, ["zergling"] * 5 + ["lurker"], (v2[0] - 80, v2[1] + 120), v0, 0.35),
         reinf(260, ["dragoon", "dragoon", "zealot", "zealot"], (v0[0] - 60, v0[1] + 280), v0),
         msg(300, "第一支援军抵达"),
         wave(390, ["ultra", "ultra", "muta", "muta", "hydra", "zergling"],
              (v1[0] - 40, v1[1] + 240), v0, 0.4),
         reinf(450, ["carrier", "templar", "dragoon"], (v0[0] - 60, v0[1] + 280), v0),
         msg(490, "航空母舰已抵达轨道"),
         wave(570, ["guardian", "guardian", "devourer", "ultra", "ultra", "ultra",
                    "hydra", "hydra", "zergling", "zergling", "zergling"],
              (v1[0], v1[1] + 240), v0, 0.35),
         lose("nexus", "星灵枢纽被摧毁")],
 aiWaves=[["zergling", "zergling", "hydra"],
          ["zergling", "hydra", "lurker"],
          ["ultra", "hydra", "hydra", "zergling"],
          ["guardian", "devourer", "ultra", "ultra", "hydra", "zergling"]]), "nexus"))

# ================================ validate ================================
OBJ_KINDS = {"destroyAll", "protect", "survive"}
ACTIONS = {"wave", "reinforce", "message", "win", "lose"}
RACES = {"terran", "zerg", "protoss"}
BUILDINGS = set()
for line in open(os.path.join(ASSETS, r"..\java\com\xjzb\rts\core\Game.java"), encoding="utf-8"):
    m = re.match(r'\s*t\("([a-z0-9_]+)",\s*"[^"]*",\s*\d+,\s*\d+,\s*\d+,\s*[\d.]+f,\s*[\d.]+f,\s*\d+,\s*\d+,\s*[\d.]+,\s*(\d+),', line)
    m = re.match(r'\s*t\("([a-z0-9_]+)",\s*"[^"]*",\s*\d+,\s*\d+,\s*\d+,\s*[\d.]+f?,\s*[\d.]+f?,\s*\d+,\s*\d+,\s*[\d.]+,\s*(\d+),', line)
    if m and int(m.group(2)) > 0: BUILDINGS.add(m.group(1))
assert "hatchery" in BUILDINGS and "cc" in BUILDINGS and "sunken" in BUILDINGS, BUILDINGS
assert "marine" not in BUILDINGS and "zergling" not in BUILDINGS
MAP_IDS = set()
for line in open(os.path.join(ASSETS, "maps", "index.txt"), encoding="utf-8"):
    p = line.strip().split("|")
    if len(p) >= 3: MAP_IDS.add(p[0])

errs = []
for m, home in M:
    where = m["id"]
    if m["map"] not in MAP_IDS: errs.append(f"{where}: map {m['map']} not in index")
    if m["playerRace"] not in RACES: errs.append(f"{where}: bad playerRace")
    if m["enemyRace"] not in RACES: errs.append(f"{where}: bad enemyRace")
    w, h, raw, starts, _u = load(m["map"])
    wm, hm = w * 4, h * 4
    keys = set()
    for su in m["startUnits"]:
        keys.add(su["type"])
        if su["type"] not in TYPES: errs.append(f"{where}: unknown type {su['type']}")
        if not (0 <= su["x"] < w * 32 and 0 <= su["y"] < h * 32):
            errs.append(f"{where}: {su['type']} out of bounds ({su['x']},{su['y']})")
        if su["type"] in BUILDINGS:
            # A building must be authored on clear ground: spawn() snaps it to
            # the tile grid but does not check walkability, so a misplaced one
            # would sit embedded in a cliff and stamp its footprint there.
            if not walk_at(raw, wm, su["x"], su["y"]):
                errs.append(f"{where}: building {su['type']} on blocked "
                            f"({su['x']},{su['y']})")
        elif not walk_at(raw, wm, su["x"], su["y"]):
            # A mobile unit is nudged to the nearest walkable minitile, the same
            # recovery the engine applies to a deferred wave spawn. The maps
            # carry single-tile pits (nightfall at 1626,412; thinice at
            # 4570,412) that a hand-authored offset can land in.
            spot = snap(raw, wm, hm, su["x"], su["y"])
            if spot is None:
                errs.append(f"{where}: {su['type']} stranded ({su['x']},{su['y']})")
            else:
                su["x"], su["y"] = spot
    homes = [su["type"] for su in m["startUnits"] if su["team"] == 0]
    if home not in homes: errs.append(f"{where}: no player {home}")
    if "hatchery" not in [su["type"] for su in m["startUnits"] if su["team"] == 1]:
        errs.append(f"{where}: enemy has no hatchery (AI anchor)")
    for o in m["objectives"]:
        if o["kind"] not in OBJ_KINDS: errs.append(f"{where}: bad objective {o['kind']}")
        if o["kind"] == "protect" and o["target"] not in keys:
            errs.append(f"{where}: protect target {o['target']} not in startUnits")
    for e in m["events"]:
        if e["action"] not in ACTIONS: errs.append(f"{where}: bad action {e['action']}")
        for u in e.get("units", []):
            if u not in TYPES: errs.append(f"{where}: event unit {u} unknown")
        for fld in ("from", "to"):
            if fld in e:
                x, y = e[fld]
                if not (0 <= x < w * 32 and 0 <= y < h * 32):
                    errs.append(f"{where}: event {fld} out of bounds {e[fld]}")
    for row in m["aiWaves"]:
        for u in row:
            if u not in TYPES: errs.append(f"{where}: aiWave unit {u} unknown")

if errs:
    print("VALIDATION FAILED:")
    for e in errs: print("  " + e)
    sys.exit(1)

for m, home in M:
    path = os.path.join(MISS, m["id"] + ".json")
    txt = json.dumps(m, indent=1, ensure_ascii=False) + "\n"
    open(path, "w", encoding="utf-8", newline="\n").write(txt)
    print("wrote %s (%s, %s vs %s, diff %d, units %d, events %d)" % (
        m["id"], m["map"], m["playerRace"], m["enemyRace"], m["difficulty"],
        len(m["startUnits"]), len(m["events"])))
print("ALL VALIDATED")

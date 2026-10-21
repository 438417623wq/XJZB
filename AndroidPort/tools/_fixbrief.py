import io
p = r"F:\KF\XJZB\AndroidPort\tools\_gen_v229_missions.py"
src = io.open(p, encoding="utf-8").read()
subs = [
 # m06: the level now HAS an economy (economy=true), so the old "no mineral
 # patch anywhere" line is false. Say what the flag actually does.
 ('  "这里没有矿脉可采——你手上的虫群就是全部家底,用它们撕开对面的巢穴。",\n'
  '  "提示:虫族的工蜂同样可以建造孵化池与地刺,但这一战你必须靠现成的部队。",',
  '  "矿脉就在巢边,工蜂已经开始采集——但别指望慢慢憋出一支大军。",\n'
  '  "对面只有一个巢穴,用你手上这支虫群直接碾过去。",'),
 # m08: only one enemy base, and it is the north one.
 ('  "夜幕降临,对面的虫群把飞龙塔搬上了高地。",',
  '  "夜幕降临,北面的虫群把飞龙塔搬上了高地。",'),
 # m09: the reinforcement spawns behind the player, not to the north.
 ('  "中途会有增援从北面抵达。"],',
  '  "中途会有增援从你身后抵达。"],'),
 # m12: one enemy base, west of the player.
 ('  "碧蓝平原的虫群正从东西两线压来。",',
  '  "碧蓝平原的虫群正从西线压来。",'),
 # m14: one hatchery, not three.
 ('  "热风的虫群把三座孵化场连成了一体。",',
  '  "热风的虫群经营了一座带完整科技树的要塞。",'),
 # m15: both enemy bases are in the southern half of the map.
 ('  "忘川。两条虫脉在南北两端各有一座主巢。",',
  '  "忘川。南面的两条虫脉各有一座主巢,互为犄角。",'),
]
for a, b in subs:
    assert src.count(a) == 1, (src.count(a), a[:60])
    src = src.replace(a, b)
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("briefings patched")
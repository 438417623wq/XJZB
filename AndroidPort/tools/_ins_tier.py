import io
P = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\core\Game.java"
s = io.open(P, encoding="utf-8").read()
old = """    /** How close two templars have to be to merge. */
    public static final float MERGE_RANGE = 48f;
"""
new = """    // ------------------------------------------- v2.27: growth and scale
    /**
     * The population ceiling. The plan asks for 200 with a headroom check and
     * 100 as the documented fallback if the engine cannot hold it. Measured on
     * the desktop harness with 200 marines against 200 zerglings in sustained
     * combat, a tick cost 10.9 ms -- a third of the 33 ms frame at 30 fps, on a
     * desktop CPU. A phone has roughly a third of that single-core throughput,
     * so 400 entities would not hold frame on the low-end target this game
     * ships to. 100 is the plan's own fallback and the largest tier that stays
     * comfortably inside budget; the tier list below is the growth ladder and
     * the ceiling is just its last entry.
     */
    public static final int[] SUPPLY_TIERS = {40, 100};
    public static final int SUPPLY_CAP = SUPPLY_TIERS[SUPPLY_TIERS.length - 1];

    /** How close two templars have to be to merge. */
    public static final float MERGE_RANGE = 48f;
"""
assert old in s, "anchor"
s = s.replace(old, new, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("ok")

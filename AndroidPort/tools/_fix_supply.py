import io
P = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\core\Game.java"
s = io.open(P, encoding="utf-8").read()
old = """    public static int supplyProvided(String key, float tier) {
        if ("cc".equals(key)) return 10;
        if ("depot".equals(key)) return 8;
        // A hatchery feeds as much as a command center, so a zerg opening is
        // not supply-starved from the first second; lair/hive are upgrades of
        // the same building and keep the same figure.
        if ("hatchery".equals(key) || "lair".equals(key) || "hive".equals(key)) return 10;
        if ("over".equals(key)) return 8;      // overlord carries supply
        // v2.10: the pylon is the protoss supply building. 8, like a depot,
        // because a protoss opening leans on a single pylon for its first
        // zealots and 10 would let the forge line run supply-free.
        if ("pylon".equals(key)) return 8;
        return 0;
    }"""
new = """    public static int supplyProvided(String key, float tier) {
        int base;
        if ("cc".equals(key)) base = 10;
        // A hatchery feeds as much as a command center, so a zerg opening is
        // not supply-starved from the first second; lair/hive are upgrades of
        // the same building and keep the same figure.
        else if ("hatchery".equals(key) || "lair".equals(key)
                || "hive".equals(key)) base = 10;
        else if ("depot".equals(key)) base = 8;
        else if ("over".equals(key)) base = 8;      // overlord carries supply
        // v2.10: the pylon is the protoss supply building. 8, like a depot,
        // because a protoss opening leans on a single pylon for its first
        // zealots and 10 would let the forge line run supply-free.
        else if ("pylon".equals(key)) base = 8;
        else return 0;
        return Math.round(base * tier);
    }"""
assert old in s, "supplyProvided block not found"
s = s.replace(old, new, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("patched supplyProvided")

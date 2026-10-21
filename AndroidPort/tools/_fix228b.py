import io
P = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\core\Game.java"
s = io.open(P, encoding="utf-8").read()
old = """        for (String k : new String[]{"scv", "marine", "firebat", "medic", "ghost",
                "vulture", "goliath", "tank", "stank", "zealot", "dragoon",
                "templar", "dtemplar", "archon", "darchon", "zergling", "hydra",
                "lurker", "lurker_bur", "ultra", "defiler", "broodling", "queen"}) {
            if (TYPES.containsKey(k)) TYPES.get(k).upClass = "infantry";
        }
        for (String k : new String[]{"wraith", "valkyrie", "battlecruiser",
                "vessel", "dropship", "scout", "corsair", "arbiter", "carrier",
                "intercep", "shuttle", "observer", "over", "muta", "guardian",
                "devourer"}) {
            if (TYPES.containsKey(k)) TYPES.get(k).upClass = "ship";
        }
        // The vehicle line is the terran mech and the protoss robotics: units
        // that walk but are not infantry. (The protoss ground line is already
        // covered by infantry above, which is the original's own grouping for
        // zealots and dragoons.)
        for (String k : new String[]{"reaver", "spider", "larva"}) {
            if (TYPES.containsKey(k)) TYPES.get(k).upClass = "vehicle";
        }"""
new = """        // infantry: the terran foot soldiers and every protoss/zerg ground
        // unit (the original groups zealots, dragoons and all zerg ground
        // under one ground-weapons line, which is the infantry tag here)
        for (String k : new String[]{"scv", "marine", "firebat", "medic", "ghost",
                "zealot", "dragoon", "templar", "dtemplar", "archon", "darchon",
                "zergling", "hydra", "lurker", "lurker_bur", "ultra", "defiler",
                "broodling", "queen", "drone"}) {
            if (TYPES.containsKey(k)) TYPES.get(k).upClass = "infantry";
        }
        // ships: every aircraft of the three races
        for (String k : new String[]{"wraith", "valkyrie", "battlecruiser",
                "vessel", "dropship", "scout", "corsair", "arbiter", "carrier",
                "intercep", "shuttle", "observer", "over", "muta", "guardian",
                "devourer"}) {
            if (TYPES.containsKey(k)) TYPES.get(k).upClass = "ship";
        }
        // vehicles: the terran mech and the protoss robotics -- units that walk
        // but are neither infantry nor aircraft.
        for (String k : new String[]{"vulture", "goliath", "tank", "stank",
                "reaver", "spider", "larva"}) {
            if (TYPES.containsKey(k)) TYPES.get(k).upClass = "vehicle";
        }"""
assert old in s, "class block"
s = s.replace(old, new, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("ok")

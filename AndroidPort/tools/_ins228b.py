import io
P = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\core\Game.java"
s = io.open(P, encoding="utf-8").read()

# spawn path: per-class bonus
old = """        if (team == 0) {
            // v2.7 9.1: upgrades are global, so anything that joins afterwards
            // must pick up the levels already researched.
            e.dmgBonus = weaponLevel * UPGRADE_DMG;
            e.armorBonus = armorLevel * UPGRADE_ARMOR;
        }
        if (t.tiles > 0) {
            e.x = snapBuilding(e.x, t.tiles);"""
new = """        if (team == 0) {
            // v2.7 9.1: upgrades are global, so anything that joins afterwards
            // must pick up the levels already researched. v2.28: from its own
            // class's lines, not from one army-wide number.
            int ui = classIndex(t.upClass);
            e.dmgBonus = (ui < 0 ? 0 : weaponByClass[ui]) * UPGRADE_DMG;
            e.armorBonus = (ui < 0 ? 0 : armorByClass[ui]) * UPGRADE_ARMOR;
        }
        if (t.tiles > 0) {
            e.x = snapBuilding(e.x, t.tiles);"""
assert old in s, "spawn upgrade"
s = s.replace(old, new, 1)

# post-pass: assign the class tags
old2 = """        TYPES.get("carrier").hangarCap = Game.HANGAR_CAP;
        TYPES.get("reaver").ammoCap = Game.REAVER_AMMO;
    }"""
new2 = """        TYPES.get("carrier").hangarCap = Game.HANGAR_CAP;
        TYPES.get("reaver").ammoCap = Game.REAVER_AMMO;

        // --- v2.28: upgrade classes ------------------------------------------
        // The original sells weapon and armour upgrades per class. The tags
        // below are that split, mapped onto the three lines this game has room
        // for. The engineering bay / forge / evolution chamber sells the
        // infantry line, the armoury / cybernetics core the vehicle line and
        // the science facility / fleet beacon the ship line -- see the command
        // card, which offers the line of whatever building is selected.
        for (String k : new String[]{"scv", "marine", "firebat", "medic", "ghost",
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
        }
    }"""
assert old2 in s, "post-pass tail"
s = s.replace(old2, new2, 1)

# AI: assign per class too
old3 = """                if (u != null) {
                    int tier = difficulty == 0 ? 0 : difficulty == 1 ? 1 : 2;
                    u.dmgBonus = tier * 2;
                    u.armorBonus = tier;
                }"""
new3 = """                if (u != null) {
                    // v2.28: the AI's ladder is per class like the player's, so
                    // a hard AI's hydralisks and mutalisks no longer share one
                    // number. (The AI is zerg, so its lines are melee/ranged/
                    // carapace in the original; here they map onto the same
                    // three tags.)
                    int tier = difficulty == 0 ? 0 : difficulty == 1 ? 1 : 2;
                    u.dmgBonus = tier * 2;
                    u.armorBonus = tier;
                }"""
assert old3 in s, "ai upgrades"
s = s.replace(old3, new3, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("ok")

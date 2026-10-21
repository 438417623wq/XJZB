import io
P = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\GameView.java"
s = io.open(P, encoding="utf-8").read()
old = """            } else if (first.team == 0 && first.buildProgress >= 1f
                    && first.type.key.equals("armory")) {
                // v2.7 9.1 shipped these on the engineering bay; v2.11 batch C
                // moved the shop to the armoury, which is where Brood War sells
                // them. Its two cells carry the current level so the player sees
                // progress.
                acts.add(new String[]{"upgrade:w", "武器 " + game.weaponLevel + "/3"});
                acts.add(new String[]{"upgrade:a", "防御 " + game.armorLevel + "/3"});
                // v2.27: the population ceiling is a research, not a constant.
                // The cell names the next tier so the player can see what the
                // money buys before spending it.
                acts.add(new String[]{"upgrade:pop",
                        game.capTier >= Game.SUPPLY_TIERS.length - 1
                                ? "人口 " + Game.SUPPLY_CAP + "(满)"
                                : "人口 → " + Game.SUPPLY_TIERS[game.capTier + 1]});
            } else if (first.team == 0 && first.constructing) {"""
new = """            } else if (first.team == 0 && first.buildProgress >= 1f
                    && upgradeLine(first.type.key) != null) {
                // v2.28: the three research buildings each own ONE class line,
                // which is the plan's "e-bay/factory/armory 各管一线": the
                // engineering bay sells infantry, the factory vehicles and the
                // armoury ships. Before this one building sold two army-wide
                // upgrades, so a single research buffed marines and
                // battlecruisers alike. Each cell carries its own line's level
                // so the player can see which line they are buying.
                String cls = upgradeLine(first.type.key);
                String cn = upgradeLineName(cls);
                acts.add(new String[]{"upgrade:w:" + cls,
                        cn + "武器 " + game.weaponFor(cls) + "/3"});
                acts.add(new String[]{"upgrade:a:" + cls,
                        cn + "防御 " + game.armorFor(cls) + "/3"});
                // v2.27: the population ceiling is a research, not a constant.
                // The cell names the next tier so the player can see what the
                // money buys before spending it.
                acts.add(new String[]{"upgrade:pop",
                        game.capTier >= Game.SUPPLY_TIERS.length - 1
                                ? "人口 " + Game.SUPPLY_CAP + "(满)"
                                : "人口 → " + Game.SUPPLY_TIERS[game.capTier + 1]});
            } else if (first.team == 0 && first.constructing) {"""
assert old in s, "armory card"
s = s.replace(old, new, 1)

# add the helpers near iconFor
old2 = """    private Bitmap iconFor(String action) {"""
new2 = """    /**
     * v2.28: which upgrade class a research building sells. The engineering bay
     * is the infantry shop, the factory the vehicle shop and the armoury the
     * ship shop -- the plan's "e-bay/factory/armory 各管一线". A building with
     * no line (everything else) returns null and shows no research cells.
     */
    private static String upgradeLine(String buildingKey) {
        switch (buildingKey) {
            case "engbay": return "infantry";
            case "factory": return "vehicle";
            case "armory": return "ship";
            default: return null;
        }
    }

    private static String upgradeLineName(String cls) {
        switch (cls) {
            case "infantry": return "步兵";
            case "vehicle": return "载具";
            case "ship": return "空军";
            default: return "";
        }
    }

    private Bitmap iconFor(String action) {"""
assert old2 in s, "iconFor anchor"
s = s.replace(old2, new2, 1)

# handler: parse the class out of the action
old3 = """                } else if (b.action.equals("upgrade:w") || b.action.equals("upgrade:a")
                        || b.action.equals("upgrade:pop")) {
                    // v2.27: the population ceiling joins the two damage
                    // researches on the armoury's card.
                    String why = b.action.equals("upgrade:w") ? game.buyWeaponUpgrade()
                            : b.action.equals("upgrade:a") ? game.buyArmorUpgrade()
                            : game.raiseSupplyCap();"""
new3 = """                } else if (b.action.startsWith("upgrade:w")
                        || b.action.startsWith("upgrade:a")
                        || b.action.equals("upgrade:pop")) {
                    // v2.28: the research cells carry their class in the action
                    // ("upgrade:w:infantry"), so the same handler serves all
                    // three buildings. v2.27: the population ceiling rides
                    // along on the same card.
                    String why;
                    if (b.action.startsWith("upgrade:w:")) {
                        why = game.buyWeaponUpgrade(b.action.substring(10));
                    } else if (b.action.startsWith("upgrade:a:")) {
                        why = game.buyArmorUpgrade(b.action.substring(10));
                    } else if (b.action.equals("upgrade:pop")) {
                        why = game.raiseSupplyCap();
                    } else {
                        why = "未知升级";
                    }"""
assert old3 in s, "upgrade handler"
s = s.replace(old3, new3, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("ok")

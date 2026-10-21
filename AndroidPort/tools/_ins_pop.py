import io
P = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\GameView.java"
s = io.open(P, encoding="utf-8").read()
old = """                acts.add(new String[]{"upgrade:w", "武器 " + game.weaponLevel + "/3"});
                acts.add(new String[]{"upgrade:a", "防御 " + game.armorLevel + "/3"});
            } else if (first.team == 0 && first.constructing) {"""
new = """                acts.add(new String[]{"upgrade:w", "武器 " + game.weaponLevel + "/3"});
                acts.add(new String[]{"upgrade:a", "防御 " + game.armorLevel + "/3"});
                // v2.27: the population ceiling is a research, not a constant.
                // The cell names the next tier so the player can see what the
                // money buys before spending it.
                acts.add(new String[]{"upgrade:pop",
                        game.capTier >= Game.SUPPLY_TIERS.length - 1
                                ? "人口 " + Game.SUPPLY_CAP + "(满)"
                                : "人口 → " + Game.SUPPLY_TIERS[game.capTier + 1]});
            } else if (first.team == 0 && first.constructing) {"""
assert old in s, "armory block"
s = s.replace(old, new, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("ok")

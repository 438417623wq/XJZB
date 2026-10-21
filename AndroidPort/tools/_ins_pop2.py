import io
P = r"F:\KF\XJZB\AndroidPort\app\app\src\main\java\com\xjzb\rts\GameView.java"
s = io.open(P, encoding="utf-8").read()
old = """                } else if (b.action.equals("upgrade:w") || b.action.equals("upgrade:a")) {
                    String why = b.action.equals("upgrade:w")
                            ? game.buyWeaponUpgrade() : game.buyArmorUpgrade();
                    if (why != null) {
                        toast = why;
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        play("build", 0.9f);
                    }
                } else if (b.action.equals("rally")) {"""
new = """                } else if (b.action.equals("upgrade:w") || b.action.equals("upgrade:a")
                        || b.action.equals("upgrade:pop")) {
                    // v2.27: the population ceiling joins the two damage
                    // researches on the armoury's card.
                    String why = b.action.equals("upgrade:w") ? game.buyWeaponUpgrade()
                            : b.action.equals("upgrade:a") ? game.buyArmorUpgrade()
                            : game.raiseSupplyCap();
                    if (why != null) {
                        toast = why;
                        toastT = 2.0f;
                        play("error", 0.9f);
                    } else {
                        if (b.action.equals("upgrade:pop")) {
                            toast = "人口上限 " + Game.SUPPLY_TIERS[game.capTier];
                            toastT = 1.8f;
                        }
                        play("build", 0.9f);
                    }
                } else if (b.action.equals("rally")) {"""
assert old in s, "upgrade handler"
s = s.replace(old, new, 1)
# the affordability/price lookup for train:/build: cells does not cover
# upgrade:pop; give it a price badge like the other two researches.
old2 = """            if ((a[0].startsWith("train:") || a[0].startsWith("build:"))) {"""
new2 = """            // v2.27: the population research shows its price like the other
            // two armoury upgrades (which are free-form, so they show none).
            if (a[0].equals("upgrade:pop")) {
                int tier = game.capTier + 1;
                Game.Type dummy = Game.TYPES.get("armory");
                afford = tier < Game.SUPPLY_TIERS.length;
                costText = afford ? String.valueOf(Game.popUpgradeCost(tier)) : null;
            }
            if ((a[0].startsWith("train:") || a[0].startsWith("build:"))) {"""
assert old2 in s, "price block"
s = s.replace(old2, new2, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("ok")

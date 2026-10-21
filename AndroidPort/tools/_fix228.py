import io
P = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
s = io.open(P, encoding="utf-8").read()
old = """        // upgrades: three levels, escalating cost, and the bonus lands on units
        g.mineralsPlayer = 1000;
        String e1 = g.buyWeaponUpgrade();
        int after1 = g.mineralsPlayer;
        String e2 = g.buyWeaponUpgrade();
        String e3 = g.buyWeaponUpgrade();
        String e4 = g.buyWeaponUpgrade();   // must refuse at max
        int bonus = marine.dmgBonus;
        System.out.println("  upgrades w=" + g.weaponLevel
                + " minerals 1000->" + after1 + "->" + g.mineralsPlayer
                + " bonus=" + bonus + " err4=" + e4
                + " PASS=" + (e1 == null && e2 == null && e3 == null && e4 != null
                              && g.weaponLevel == 3 && bonus == 6
                              && g.mineralsPlayer == 1000 - 450));"""
new = """        // upgrades: three levels, escalating cost, and the bonus lands on the
        // units of the line that was researched (v2.28: per class, so the
        // marine's infantry line is what this exercises).
        g.mineralsPlayer = 1000;
        String e1 = g.buyWeaponUpgrade(marine);
        int after1 = g.mineralsPlayer;
        String e2 = g.buyWeaponUpgrade(marine);
        String e3 = g.buyWeaponUpgrade(marine);
        String e4 = g.buyWeaponUpgrade(marine);   // must refuse at max
        int bonus = marine.dmgBonus;
        System.out.println("  upgrades w=" + g.weaponLevel
                + " minerals 1000->" + after1 + "->" + g.mineralsPlayer
                + " bonus=" + bonus + " err4=" + e4
                + " PASS=" + (e1 == null && e2 == null && e3 == null && e4 != null
                              && g.weaponLevel == 3 && bonus == 6
                              && g.mineralsPlayer == 1000 - 450));"""
assert old in s, "upgrade assert"
s = s.replace(old, new, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("ok")

import io
P = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
s = io.open(P, encoding="utf-8").read()
anchor = """        System.out.println("[v227]");
        v227Tests();
"""
assert anchor in s
s = s.replace(anchor, anchor + """
        System.out.println("[v228]");
        v228Tests();
""", 1)
anchor2 = """        System.out.println("  groups/population" + sb + " PASS=" + ok);
    }
"""
assert anchor2 in s
method = '''
    /**
     * v2.28: the upgrade lines are per class.
     *
     *   split -- researching the infantry weapon line raises a marine's bonus
     *     and leaves a siege tank's alone (the old single axis buffed both);
     *   independence -- the three lines level separately, so buying ships does
     *     not move the infantry figure;
     *   save -- the per-class levels survive a round trip, and a save written
     *     before the split still loads (the arrays default to zero).
     */
    static void v228Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        com.xjzb.rts.core.Game g = cleanGame("terran");
        com.xjzb.rts.core.Game.Ent inf = g.spawn("marine", 0, 500, 500, true);
        com.xjzb.rts.core.Game.Ent veh = g.spawn("tank", 0, 540, 500, true);
        com.xjzb.rts.core.Game.Ent shp = g.spawn("wraith", 0, 580, 500, true);
        boolean tagged = "infantry".equals(inf.type.upClass)
                && "vehicle".equals(veh.type.upClass)
                && "ship".equals(shp.type.upClass);
        int inf0 = inf.dmgBonus, veh0 = veh.dmgBonus, shp0 = shp.dmgBonus;

        // buy two infantry weapon levels
        g.mineralsPlayer = 5000;
        boolean b1 = g.buyWeaponUpgrade(inf) == null;
        boolean b2 = g.buyWeaponUpgrade(inf) == null;
        int infAfter = inf.dmgBonus, vehAfter = veh.dmgBonus, shpAfter = shp.dmgBonus;
        // only the infantry line moved
        boolean onlyInf = b1 && b2 && infAfter == inf0 + 4
                && vehAfter == veh0 && shpAfter == shp0;
        boolean levels = g.weaponFor("infantry") == 2
                && g.weaponFor("vehicle") == 0 && g.weaponFor("ship") == 0;
        ok &= tagged && onlyInf && levels;
        sb.append(" tagged=").append(tagged)
          .append(" inf=").append(inf0).append("->").append(infAfter)
          .append(" veh=").append(vehAfter).append(" shp=").append(shpAfter)
          .append(" levels=").append(levels);

        // the ship line levels on its own, and does not disturb infantry
        boolean s1 = g.buyWeaponUpgrade(shp) == null;
        boolean s2 = g.buyWeaponUpgrade(shp) == null;
        boolean s3 = g.buyWeaponUpgrade(shp) == null;
        boolean shipMax = s1 && s2 && s3 && g.weaponFor("ship") == 3
                && shp.dmgBonus == shp0 + 6 && inf.dmgBonus == infAfter;
        // and it refuses a fourth
        boolean shipRefuse = g.buyWeaponUpgrade(shp) != null;
        ok &= shipMax && shipRefuse;
        sb.append(" ship=").append(shp0).append("->").append(shp.dmgBonus)
          .append(" max=").append(shipMax).append(" refuse4=").append(shipRefuse);

        // armour is per class too
        int infArm0 = inf.armorBonus;
        g.mineralsPlayer = 5000;
        boolean a1 = g.buyArmorUpgrade(veh) == null;
        boolean a2 = g.buyArmorUpgrade(veh) == null;
        boolean armorSplit = a1 && a2 && veh.armorBonus == 2
                && inf.armorBonus == infArm0;
        // the aggregate the HUD reads is the max across the lines
        boolean agg = g.weaponLevel == 3 && g.armorLevel == 2;
        ok &= armorSplit && agg;
        sb.append(" armorSplit=").append(armorSplit).append(" aggregate=").append(agg);

        // a building has no line and is refused
        com.xjzb.rts.core.Game.Ent cc = g.spawn("cc", 0, 400, 400, true);
        boolean buildingRefused = "".equals(cc.type.upClass)
                && g.buyWeaponUpgrade(cc) != null;

        // ---- the split survives a save/load round trip ----------------------
        String blob = g.serialize();
        com.xjzb.rts.core.Game back = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, elev, starts, units, "terran");
        boolean loaded = back.deserialize(blob);
        boolean kept = loaded
                && back.weaponFor("infantry") == 2
                && back.weaponFor("ship") == 3
                && back.armorFor("vehicle") == 2
                && back.armorFor("infantry") == 0;
        // a v2.27-shaped save (no per-class tokens) still loads, at level 0
        String legacy = "XJZB-SAVE-1\\nstate 400 0 3.0 1 300 60.0 0 5.0 0 0 0 0 0 0 terran 0\\n";
        com.xjzb.rts.core.Game old = new com.xjzb.rts.core.Game(
                mapW, mapH, walk, elev, starts, units, "terran");
        boolean legacyOk = old.deserialize(legacy)
                && old.weaponFor("infantry") == 0 && old.capTier == 0;
        ok &= buildingRefused && kept && legacyOk;
        sb.append(" buildingRefused=").append(buildingRefused)
          .append(" saveKept=").append(kept).append(" legacyLoads=").append(legacyOk);

        System.out.println("  upgrade lines" + sb + " PASS=" + ok);
    }
'''
s = s.replace(anchor2, anchor2 + method, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("ok")

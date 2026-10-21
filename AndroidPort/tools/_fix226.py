import io
P = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
s = io.open(P, encoding="utf-8").read()
old = """        // ---- burrow: hide, stay safe from melee, still shootable ------------
        com.xjzb.rts.core.Game bg = cleanGame("zerg");
        com.xjzb.rts.core.Game.Ent ling = bg.spawn("zergling", 0, 600, 600, true);
        boolean canB = com.xjzb.rts.core.Game.canBurrow(ling);
        boolean down = bg.toggleBurrow(ling);
        boolean hidden = ling.burrowed && ling.cloakActive;
        // a marine (ranged) can still target it, a zealot (melee) cannot
        com.xjzb.rts.core.Game.Ent marine = bg.spawn("marine", 1, 640, 600, true);
        com.xjzb.rts.core.Game.Ent zealot = bg.spawn("zealot", 1, 640, 600, true);
        bg.update(1 / 30f);
        boolean rangedSees = bg.findEnemyInRange(marine, 400) == ling;
        boolean meleeBlind = bg.findEnemyInRange(zealot, 400) != ling;
        // and it comes back up
        boolean up = bg.toggleBurrow(ling) && !ling.burrowed;
        // a non-zerg unit cannot burrow at all
        com.xjzb.rts.core.Game.Ent m2 = bg.spawn("marine", 0, 700, 600, true);
        boolean refuse = !com.xjzb.rts.core.Game.canBurrow(m2)
                && bg.burrowError(m2) != null;
        ok &= canB && down && hidden && rangedSees && meleeBlind && up && refuse;
        sb.append(" burrow=").append(down).append(" hidden=").append(hidden)
          .append(" rangedSees=").append(rangedSees).append(" meleeBlind=").append(meleeBlind)
          .append(" unburrow=").append(up).append(" refuse=").append(refuse);
"""
new = """        // ---- burrow: hide from everything until a detector shows up --------
        // A burrowed unit joins the cloak layer (isCloakedNow), so the single
        // gate in findEnemyInRange hides it from melee AND ranged alike until
        // one of the enemy's detectors is in reach -- which is the original's
        // rule, and the reason the missile turret is worth building.
        com.xjzb.rts.core.Game bg = cleanGame("zerg");
        com.xjzb.rts.core.Game.Ent ling = bg.spawn("zergling", 0, 600, 600, true);
        boolean canB = com.xjzb.rts.core.Game.canBurrow(ling);
        boolean down = bg.toggleBurrow(ling);
        boolean hidden = ling.burrowed && ling.cloakActive && !ling.spotted;
        com.xjzb.rts.core.Game.Ent marine = bg.spawn("marine", 1, 640, 600, true);
        com.xjzb.rts.core.Game.Ent zealot = bg.spawn("zealot", 1, 640, 600, true);
        bg.update(1 / 30f);
        boolean rangedBlind = bg.findEnemyInRange(marine, 400) != ling;
        boolean meleeBlind = bg.findEnemyInRange(zealot, 400) != ling;
        // a detector (a player missile turret) reveals it to both
        com.xjzb.rts.core.Game.Ent turret = bg.spawn("turret", 0, 640, 600, true);
        bg.update(1 / 30f);
        boolean spotted = ling.spotted;
        boolean rangedSees = bg.findEnemyInRange(marine, 400) == ling;
        // and it comes back up, becoming visible to everything again
        turret.hp = 0;
        boolean up = bg.toggleBurrow(ling) && !ling.burrowed;
        bg.update(1 / 30f);
        boolean visibleAgain = !ling.cloakActive;
        // a non-zerg unit cannot burrow at all
        com.xjzb.rts.core.Game.Ent m2 = bg.spawn("marine", 0, 700, 600, true);
        boolean refuse = !com.xjzb.rts.core.Game.canBurrow(m2)
                && bg.burrowError(m2) != null;
        ok &= canB && down && hidden && rangedBlind && meleeBlind && spotted
                && rangedSees && up && visibleAgain && refuse;
        sb.append(" burrow=").append(down).append(" hidden=").append(hidden)
          .append(" blind(noDetector)=").append(rangedBlind && meleeBlind)
          .append(" spotted=").append(spotted).append(" seesAfterDetector=").append(rangedSees)
          .append(" unburrow=").append(up).append(" refuse=").append(refuse);
"""
assert old in s, "burrow block not found"
s = s.replace(old, new, 1)

old2 = """        com.xjzb.rts.core.Game.Ent reaver = rg.spawn("reaver", 0, 600, 600, true);
        boolean fullRack = reaver.ammo == com.xjzb.rts.core.Game.REAVER_AMMO;
        rg.spawn("zergling", 1, 640, 600, true);
        // drain the rack
        for (int i = 0; i < com.xjzb.rts.core.Game.REAVER_AMMO; i++) {
            reaver.cd = 0;
            rg.update(1 / 30f);
        }
        boolean emptied = reaver.ammo == 0;
"""
new2 = """        com.xjzb.rts.core.Game.Ent reaver = rg.spawn("reaver", 0, 600, 600, true);
        boolean fullRack = reaver.ammo == com.xjzb.rts.core.Game.REAVER_AMMO;
        // A 400 hp ultralisk soaks all ten scarabs; a 35 hp zergling would die
        // after four and the rack would never actually empty.
        com.xjzb.rts.core.Game.Ent soak = rg.spawn("ultra", 1, 640, 600, true);
        // drain the rack
        for (int i = 0; i < 200 && reaver.ammo > 0; i++) {
            reaver.cd = 0;
            rg.update(1 / 30f);
        }
        boolean emptied = reaver.ammo == 0;
"""
assert old2 in s, "reaver block not found"
s = s.replace(old2, new2, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("patched")

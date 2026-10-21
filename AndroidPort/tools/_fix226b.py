import io
P = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
s = io.open(P, encoding="utf-8").read()

# 1) dark merge: bring the pair together before merging (refuseFar is checked
#    on the same two units while they are still apart).
old = """        boolean refuseFar = mg.mergeError(far, null) != null;
        // and the dark pair does merge, into the dark archon
        com.xjzb.rts.core.Game.Ent darchon = mg.orderMerge(far, null);"""
new = """        boolean refuseFar = mg.mergeError(far, null) != null;
        // and the dark pair does merge, into the dark archon -- once they are
        // standing together (the far check above used them while apart)
        dt2.x = dt1.x + 20;
        com.xjzb.rts.core.Game.Ent darchon = mg.orderMerge(far, null);"""
assert old in s, "dark merge block"
s = s.replace(old, new, 1)

# 2) burrow: settle the cloak layer after toggling, and put the detector on the
#    ENEMY team (a team-0 detector reveals team-1 cloaks, not its own side).
old2 = """        boolean down = bg.toggleBurrow(ling);
        boolean hidden = ling.burrowed && ling.cloakActive && !ling.spotted;
        com.xjzb.rts.core.Game.Ent marine = bg.spawn("marine", 1, 640, 600, true);
        com.xjzb.rts.core.Game.Ent zealot = bg.spawn("zealot", 1, 640, 600, true);
        bg.update(1 / 30f);
        boolean rangedBlind = bg.findEnemyInRange(marine, 400) != ling;
        boolean meleeBlind = bg.findEnemyInRange(zealot, 400) != ling;
        // a detector (a player missile turret) reveals it to both
        com.xjzb.rts.core.Game.Ent turret = bg.spawn("turret", 0, 640, 600, true);
        bg.update(1 / 30f);"""
new2 = """        boolean down = bg.toggleBurrow(ling);
        com.xjzb.rts.core.Game.Ent marine = bg.spawn("marine", 1, 640, 600, true);
        com.xjzb.rts.core.Game.Ent zealot = bg.spawn("zealot", 1, 640, 600, true);
        bg.update(1 / 30f);      // settle the cloak layer the toggle feeds
        boolean hidden = ling.burrowed && ling.cloakActive && !ling.spotted;
        boolean rangedBlind = bg.findEnemyInRange(marine, 400) != ling;
        boolean meleeBlind = bg.findEnemyInRange(zealot, 400) != ling;
        // an ENEMY detector reveals it (detectorNear asks for the opposite
        // team, so a friendly turret would prove nothing)
        com.xjzb.rts.core.Game.Ent turret = bg.spawn("turret", 1, 640, 600, true);
        bg.update(1 / 30f);"""
assert old2 in s, "burrow block"
s = s.replace(old2, new2, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("patched")

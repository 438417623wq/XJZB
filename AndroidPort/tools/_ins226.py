import io
P = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
s = io.open(P, encoding="utf-8").read()
anchor = "        System.out.println(\"  addons/scan/nuke\" + sb + \" PASS=\" + ok);\n    }\n"
assert anchor in s, "anchor not found"
method = '''
    /**
     * v2.26: production fidelity.
     *
     *   merge -- two same-type templars standing together become one archon,
     *     both are consumed, mismatched pairs and distant pairs are refused;
     *   burrow -- any zerg ground unit can hide, a burrowed unit is invisible
     *     and untouchable by melee but still reachable by ranged fire;
     *   hangar -- a carrier fills its hangar over time and launches the
     *     interceptors only while an enemy is in range;
     *   ammo -- a reaver carries a finite rack, cannot fire empty, and reloads
     *     only beside its robotics facility.
     */
    static void v226Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();

        // ---- merge: two templars -> one archon -----------------------------
        com.xjzb.rts.core.Game mg = cleanGame("protoss");
        com.xjzb.rts.core.Game.Ent t1 = mg.spawn("templar", 0, 600, 600, true);
        com.xjzb.rts.core.Game.Ent t2 = mg.spawn("templar", 0, 620, 600, true);
        List<com.xjzb.rts.core.Game.Ent> pair = new ArrayList<>();
        pair.add(t1);
        pair.add(t2);
        int before = mg.ents.size();
        com.xjzb.rts.core.Game.Ent archon = mg.orderMerge(pair, null);
        mg.update(1 / 30f);
        boolean merged = archon != null && "archon".equals(archon.type.key);
        // two in, one out: the two templars are gone and the archon stands
        boolean consumed = !t1.alive() && !t2.alive();
        boolean oneLeft = mg.ents.size() == before - 1;
        // the archon keeps its shield (350) and 10 hp, the original's shape
        boolean shape = archon != null && archon.type.shield == 350
                && archon.type.hp == 10 && archon.shield == 350;
        ok &= merged && consumed && oneLeft && shape;
        sb.append(" merge=").append(merged).append(" consumed=").append(consumed)
          .append(" oneLeft=").append(oneLeft).append(" shape=").append(shape);

        // mismatched pair and distant pair are refused
        com.xjzb.rts.core.Game.Ent dt1 = mg.spawn("dtemplar", 0, 700, 600, true);
        com.xjzb.rts.core.Game.Ent zl = mg.spawn("zealot", 0, 720, 600, true);
        List<com.xjzb.rts.core.Game.Ent> bad = new ArrayList<>();
        bad.add(dt1);
        bad.add(zl);
        boolean refuseMix = mg.mergeError(bad, null) != null;
        com.xjzb.rts.core.Game.Ent dt2 = mg.spawn("dtemplar", 0, 900, 600, true);
        List<com.xjzb.rts.core.Game.Ent> far = new ArrayList<>();
        far.add(dt1);
        far.add(dt2);
        boolean refuseFar = mg.mergeError(far, null) != null;
        // and the dark pair does merge, into the dark archon
        com.xjzb.rts.core.Game.Ent darchon = mg.orderMerge(far, null);
        boolean darkMerge = darchon != null && "darchon".equals(darchon.type.key);
        ok &= refuseMix && refuseFar && darkMerge;
        sb.append(" refuseMix=").append(refuseMix).append(" refuseFar=").append(refuseFar)
          .append(" darkMerge=").append(darkMerge);

        // ---- burrow: hide, stay safe from melee, still shootable ------------
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

        // ---- carrier hangar -------------------------------------------------
        com.xjzb.rts.core.Game hg = cleanGame("protoss");
        com.xjzb.rts.core.Game.Ent carrier = hg.spawn("carrier", 0, 600, 600, true);
        int start = carrier.interceptors;
        for (int i = 0; i < 30 * 30; i++) hg.update(1 / 30f);
        boolean filled = carrier.interceptors == com.xjzb.rts.core.Game.HANGAR_CAP;
        boolean idle = carrier.launched == 0;      // nothing to shoot
        com.xjzb.rts.core.Game.Ent foe = hg.spawn("zergling", 1, 660, 600, true);
        hg.update(1 / 30f);
        boolean launched = carrier.launched == carrier.interceptors;
        // and it recalls them once the coast is clear
        foe.hp = 0;
        hg.update(1 / 30f);
        boolean recalled = carrier.launched == 0;
        ok &= filled && idle && launched && recalled;
        sb.append(" hangar=").append(start).append("->").append(carrier.interceptors)
          .append(" idle=").append(idle).append(" launched=").append(launched)
          .append(" recalled=").append(recalled);

        // ---- reaver scarab rack ---------------------------------------------
        com.xjzb.rts.core.Game rg = cleanGame("protoss");
        com.xjzb.rts.core.Game.Ent reaver = rg.spawn("reaver", 0, 600, 600, true);
        boolean fullRack = reaver.ammo == com.xjzb.rts.core.Game.REAVER_AMMO;
        rg.spawn("zergling", 1, 640, 600, true);
        // drain the rack
        for (int i = 0; i < com.xjzb.rts.core.Game.REAVER_AMMO; i++) {
            reaver.cd = 0;
            rg.update(1 / 30f);
        }
        boolean emptied = reaver.ammo == 0;
        // empty and far from a robotics bay: no reload
        for (int i = 0; i < 30 * 30; i++) rg.update(1 / 30f);
        boolean stillEmpty = reaver.ammo == 0;
        // beside a robotics bay it reloads
        rg.spawn("robotic", 0, reaver.x + 40, reaver.y, true);
        for (int i = 0; i < (int) (com.xjzb.rts.core.Game.REAVER_RELOAD_TIME * 30) + 90; i++)
            rg.update(1 / 30f);
        boolean reloaded = reaver.ammo > 0;
        ok &= fullRack && emptied && stillEmpty && reloaded;
        sb.append(" rack=").append(fullRack).append(" emptied=").append(emptied)
          .append(" noReloadAway=").append(stillEmpty).append(" reloaded=").append(reloaded);

        System.out.println("  merge/burrow/hangar/ammo" + sb + " PASS=" + ok);
    }
'''
s = s.replace(anchor, anchor + method, 1)
io.open(P, "w", encoding="utf-8").write(s)
print("inserted, new length", len(s))

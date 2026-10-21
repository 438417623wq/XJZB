import io
p = r"F:\KF\XJZB\AndroidPort\tools\GameDesktop.java"
src = io.open(p, encoding="utf-8").read()

old_a = '''            for (Object[] u : m.startUnits) {
                String key = (String) u[0];
                startKeys.add(key);
                if (!com.xjzb.rts.core.Game.TYPES.containsKey(key)) unknownUnits++;
                int team = (Integer) u[3];
                float x = (Float) u[1], y = (Float) u[2];
                if (x < 0 || y < 0 || x >= mw * 32 || y >= mh * 32) { offMap++; System.out.println("    OFFMAP start " + id + " " + key + " " + x + "," + y + " map=" + mw + "x" + mh); }
                else if (!walkM[((int) (y / 8)) * mw * 4 + (int) (x / 8)]) { blocked++; System.out.println("    BLOCKED start " + id + " " + key + " " + x + "," + y); }
                if (team == 0 && ("cc".equals(key) || "hatchery".equals(key)
                        || "nexus".equals(key))) playerHall = true;
                if (team == 1 && "hatchery".equals(key)) enemyHall = true;
            }
'''
new_a = '''            for (Object[] u : m.startUnits) {
                String key = (String) u[0];
                startKeys.add(key);
                com.xjzb.rts.core.Game.Type ty = com.xjzb.rts.core.Game.TYPES.get(key);
                if (ty == null) unknownUnits++;
                int team = (Integer) u[3];
                float x = (Float) u[1], y = (Float) u[2];
                if (x < 0 || y < 0 || x >= mw * 32 || y >= mh * 32) offMap++;
                // A building has to be authored on clear ground: spawn() snaps
                // it to the tile grid and stamps its footprint there, so one
                // sitting in a cliff stays in the cliff. A mobile unit is
                // allowed a single-tile pit -- setMission nudges it out, the
                // same recovery Mission.update applies to a wave spawn -- so it
                // is checked against the built game below instead.
                else if (ty != null && ty.tiles > 0
                        && !walkM[((int) (y / 8)) * mw * 4 + (int) (x / 8)]) blocked++;
                if (team == 0 && ("cc".equals(key) || "hatchery".equals(key)
                        || "nexus".equals(key))) playerHall = true;
                if (team == 1 && "hatchery".equals(key)) enemyHall = true;
            }
'''
assert src.count(old_a) == 1, src.count(old_a)
src = src.replace(old_a, new_a)

old_b = '''                    if (pt != null && (pt[0] < 0 || pt[1] < 0
                            || pt[0] >= mw * 32 || pt[1] >= mh * 32)) { offMap++; System.out.println("    OFFMAP event " + id + " " + e.action + " " + pt[0] + "," + pt[1] + " map=" + mw + "x" + mh); }
'''
new_b = '''                    if (pt != null && (pt[0] < 0 || pt[1] < 0
                            || pt[0] >= mw * 32 || pt[1] >= mh * 32)) offMap++;
'''
assert src.count(old_b) == 1, src.count(old_b)
src = src.replace(old_b, new_b)

old_c = '''            // #9: the economy flag really does rebuild the map's mineral rows
            if (m.economy) {
                com.xjzb.rts.core.Game g = missionGame(id);
                if (g.minerals.isEmpty()) ecoMiss++;
            }
'''
new_c = '''            // #8/#9: build the level and ask the engine two things -- is any
            // mobile unit standing inside terrain, and did an economy mission
            // really get the map's mineral fields back.
            com.xjzb.rts.core.Game g = missionGame(id);
            for (com.xjzb.rts.core.Game.Ent e : g.ents)
                if (e.type.tiles == 0
                        && !g.passMini((int) (e.x / 8), (int) (e.y / 8))) stranded++;
            if (m.economy && g.minerals.isEmpty()) ecoMiss++;
'''
assert src.count(old_c) == 1, src.count(old_c)
src = src.replace(old_c, new_c)

old_d = '''        int n = 0, unknownUnits = 0, badMap = 0, badRace = 0, badKind = 0,
                noEnemyHall = 0, noPlayerHall = 0, badProtect = 0, offMap = 0,
                blocked = 0, ecoMiss = 0, indexMismatch = 0;
'''
new_d = '''        int n = 0, unknownUnits = 0, badMap = 0, badRace = 0, badKind = 0,
                noEnemyHall = 0, noPlayerHall = 0, badProtect = 0, offMap = 0,
                blocked = 0, stranded = 0, ecoMiss = 0, indexMismatch = 0;
'''
assert src.count(old_d) == 1, src.count(old_d)
src = src.replace(old_d, new_d)

old_e = '''                && noPlayerHall == 0 && badProtect == 0 && offMap == 0
                && blocked == 0 && ecoMiss == 0;
'''
new_e = '''                && noPlayerHall == 0 && badProtect == 0 && offMap == 0
                && blocked == 0 && stranded == 0 && ecoMiss == 0;
'''
assert src.count(old_e) == 1, src.count(old_e)
src = src.replace(old_e, new_e)

old_f = '''          .append(" blocked=").append(blocked)
          .append(" economy=").append(ecoMiss);
'''
new_f = '''          .append(" blocked=").append(blocked)
          .append(" stranded=").append(stranded)
          .append(" economy=").append(ecoMiss);
'''
assert src.count(old_f) == 1, src.count(old_f)
src = src.replace(old_f, new_f)

io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("v229Tests restructured")
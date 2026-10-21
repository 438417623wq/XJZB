    /**
     * v2.36: can every mission actually be won?
     *
     * [v229] proves each mission's DATA is well-formed -- keys exist, coordinates
     * are on the map, buildings sit on clear ground. None of that says a level
     * can be WON. The trap is the one the map pipeline was built around: if the
     * player's base and an enemy base sit on separate landmasses the player can
     * never reach that enemy, and a destroyAll objective becomes unreachable no
     * matter how well the player plays. The shipped map pool was filtered for
     * exactly this, but a mission authors its OWN coordinates, so the property
     * has to be checked per mission rather than inherited from the map.
     *
     * This is not hypothetical: it found m05. That level ships a second enemy
     * outpost whose hatchery snapped onto a tile inside a 28-minitile pocket
     * that the player's region does not contain, while m05's objective is
     * destroyAll -- so the level could not be completed at all. It had been that
     * way since the level was authored.
     *
     * The reachability test is the project's own: the same 8-connectivity plus
     * one-cell dilation that pipeline_maps.py's start-connectivity gate uses.
     * Game.findPath is deliberately NOT used here -- it is a short-range unit
     * pather with a 60000-expansion cap, and across a 128x128 map it gives up
     * and reports "no path" for two bases that are plainly connected.
     *
     * Scope, on purpose: every destroyAll level is checked, because its objective
     * IS reachability. A survive or protect level (m01, m08, m12) is not checked,
     * and that is not a hole: m01's enemy reaches the player by SCRIPTED wave
     * spawns at a fixed point rather than by pathing (see Mission.fire), so its
     * landmass layout does not gate the level. m01 does sit on two landmasses,
     * which is fine -- the player is not required to go anywhere.
     */
    static void v236Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();
        int checked = 0, destroyLevels = 0, unreachable = 0;
        StringBuilder bad = new StringBuilder();

        for (String row : Files.readAllLines(Paths.get(ASSETS + "/missions/index.txt"))) {
            String[] f = row.trim().split("\\|");
            if (f.length < 3) continue;
            String id = f[0];
            com.xjzb.rts.core.Game g = missionGame(id);
            if (g == null || g.mission == null) continue;

            boolean destroy = false;
            for (com.xjzb.rts.core.Mission.Objective o : g.mission.objectives)
                if ("destroyAll".equals(o.kind)) destroy = true;
            if (!destroy) continue;
            destroyLevels++;

            // the player's region, using the pipeline's connectivity rule
            com.xjzb.rts.core.Game.Ent hall = null;
            for (com.xjzb.rts.core.Game.Ent e : g.ents)
                if (e.team == 0 && hall == null && ("cc".equals(e.type.key)
                        || "hatchery".equals(e.type.key) || "nexus".equals(e.type.key)))
                    hall = e;
            if (hall == null) { unreachable++; bad.append(" ").append(id).append("(noHall)"); continue; }

            int w = g.wMini, h = g.hMini;
            boolean[] usable = new boolean[w * h];
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++) {
                    if (g.passMini(x, y)) { usable[y * w + x] = true; continue; }
                    for (int dy = -1; dy <= 1 && !usable[y * w + x]; dy++)
                        for (int dx = -1; dx <= 1; dx++) {
                            int X = x + dx, Y = y + dy;
                            if (X < 0 || Y < 0 || X >= w || Y >= h) continue;
                            if (g.passMini(X, Y)) { usable[y * w + x] = true; break; }
                        }
                }
            int[] start = g.nearestPassMini((int) (hall.x / 8), (int) (hall.y / 8), 40);
            boolean[] seen = new boolean[w * h];
            java.util.ArrayDeque<int[]> q = new java.util.ArrayDeque<>();
            q.add(start);
            seen[start[1] * w + start[0]] = true;
            int[][] D = {{1,0},{-1,0},{0,1},{0,-1},{1,1},{1,-1},{-1,1},{-1,-1}};
            while (!q.isEmpty()) {
                int[] p = q.poll();
                for (int[] d : D) {
                    int X = p[0] + d[0], Y = p[1] + d[1];
                    if (X < 0 || Y < 0 || X >= w || Y >= h) continue;
                    if (seen[Y * w + X] || !usable[Y * w + X]) continue;
                    seen[Y * w + X] = true;
                    q.add(new int[]{X, Y});
                }
            }

            // every enemy hatchery must sit in the player's region
            for (com.xjzb.rts.core.Game.Ent e : g.ents) {
                if (e.team != 1 || !"hatchery".equals(e.type.key)) continue;
                checked++;
                // the hatchery's own tile is blocked by its own footprint, so
                // snap out of it before testing membership
                int[] fs = g.nearestPassMini((int) (e.x / 8), (int) (e.y / 8), 40);
                if (fs == null || !seen[fs[1] * w + fs[0]]) {
                    unreachable++;
                    bad.append(" ").append(id).append("@")
                       .append((int) e.x).append(",").append((int) e.y);
                }
            }
        }

        ok &= destroyLevels >= 11 && checked >= 12 && unreachable == 0;
        sb.append(" destroyLevels=").append(destroyLevels)
          .append(" hallsChecked=").append(checked)
          .append(" unreachable=").append(unreachable);
        if (bad.length() > 0) sb.append(" bad:").append(bad);
        System.out.println("  mission reachability" + sb + " PASS=" + ok);
    }

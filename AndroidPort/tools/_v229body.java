    /**
     * v2.29: the campaign expansion. Ten new missions (m06-m15) ship as data,
     * so the risk here is not logic but a typo: `setMission` skips an unknown
     * unit key with a bare `continue` and a wave event drops it silently, so a
     * misspelt "hydrlisk" yields a level that looks fine and simply fights with
     * one unit fewer. This walk validates every mission in index.txt against
     * the engine's own tables and the map assets each one names.
     *
     *  #1 the index row and the JSON agree (id, map) and the map exists;
     *  #2 both races are real race keys;
     *  #3 every unit key -- start units, wave/reinforce units, aiWaves -- exists
     *     in Game.TYPES;
     *  #4 every objective kind and event action is one the parser handles;
     *  #5 every level has a player town hall and an enemy hatchery. The enemy
     *     one is not cosmetic: the AI's production drain, its rally point and
     *     its structure ladder are all anchored on a hatchery (Game.java:5548,
     *     5690, 5957), so a level without one fields an enemy that never moves;
     *  #6 a protect target is actually on the board at start, or the objective
     *     fails on the first frame;
     *  #7 every authored coordinate is inside the map;
     *  #8 every start unit stands on walkable ground, checked against the map's
     *     own walk bitmap -- the same data the runtime reads;
     *  #9 an "economy": true mission really gets its mineral fields back.
     */
    static void v229Tests() throws Exception {
        boolean ok = true;
        StringBuilder sb = new StringBuilder();
        java.util.Set<String> mapIds = new java.util.HashSet<>();
        for (String line : Files.readAllLines(Paths.get(ASSETS + "/maps/index.txt"))) {
            String[] p = line.trim().split("\\|");
            if (p.length >= 3) mapIds.add(p[0]);
        }
        java.util.Set<String> races = new java.util.HashSet<>(
                java.util.Arrays.asList("terran", "zerg", "protoss"));
        java.util.Set<String> objKinds = new java.util.HashSet<>(
                java.util.Arrays.asList("destroyAll", "protect", "survive"));
        java.util.Set<String> actions = new java.util.HashSet<>(
                java.util.Arrays.asList("wave", "reinforce", "message", "win", "lose"));

        int n = 0, unknownUnits = 0, badMap = 0, badRace = 0, badKind = 0,
                noEnemyHall = 0, noPlayerHall = 0, badProtect = 0, offMap = 0,
                blocked = 0, ecoMiss = 0, indexMismatch = 0;

        for (String row : Files.readAllLines(Paths.get(ASSETS + "/missions/index.txt"))) {
            String[] f = row.trim().split("\\|");
            if (f.length < 3) continue;
            n++;
            String id = f[0];
            java.nio.file.Path jp = Paths.get(ASSETS + "/missions/" + id + ".json");
            if (!Files.exists(jp)) { indexMismatch++; continue; }
            com.xjzb.rts.core.Mission m = com.xjzb.rts.core.Mission.parse(
                    new String(Files.readAllBytes(jp), java.nio.charset.StandardCharsets.UTF_8));
            if (m == null) { indexMismatch++; continue; }
            if (!id.equals(m.id) || !f[2].trim().equals(m.map)) indexMismatch++;
            if (!mapIds.contains(m.map)) { badMap++; continue; }
            if (!races.contains(m.playerRace) || !races.contains(m.enemyRace)) badRace++;

            // the map's own terrain: the same meta.txt and walk bitmap the
            // runtime loads, so "on walkable ground" means what it says.
            String meta = new String(Files.readAllBytes(
                    Paths.get(ASSETS + "/maps/" + m.map + "/meta.txt")),
                    java.nio.charset.StandardCharsets.UTF_8);
            int mw = 0, mh = 0;
            for (String ln : meta.split("\n")) {
                ln = ln.trim();
                if (ln.startsWith("w=")) mw = Integer.parseInt(ln.substring(2));
                else if (ln.startsWith("h=")) mh = Integer.parseInt(ln.substring(2));
            }
            boolean[] walkM = new boolean[mw * 4 * mh * 4];
            java.io.InputStream in = new java.util.zip.GZIPInputStream(
                    Files.newInputStream(Paths.get(ASSETS + "/maps/" + m.map + "/walk.bin.gz")));
            byte[] raw = in.readAllBytes();
            in.close();
            for (int i = 0; i < raw.length && i < walkM.length; i++) walkM[i] = raw[i] != 0;

            boolean playerHall = false, enemyHall = false;
            java.util.Set<String> startKeys = new java.util.HashSet<>();
            for (Object[] u : m.startUnits) {
                String key = (String) u[0];
                startKeys.add(key);
                if (!com.xjzb.rts.core.Game.TYPES.containsKey(key)) unknownUnits++;
                int team = (Integer) u[3];
                float x = (Float) u[1], y = (Float) u[2];
                if (x < 0 || y < 0 || x >= mw * 32 || y >= mh * 32) offMap++;
                else if (!walkM[((int) (y / 8)) * mw * 4 + (int) (x / 8)]) blocked++;
                if (team == 0 && ("cc".equals(key) || "hatchery".equals(key)
                        || "nexus".equals(key))) playerHall = true;
                if (team == 1 && "hatchery".equals(key)) enemyHall = true;
            }
            if (!playerHall) noPlayerHall++;
            if (!enemyHall) noEnemyHall++;
            for (com.xjzb.rts.core.Mission.Objective o : m.objectives) {
                if (!objKinds.contains(o.kind)) badKind++;
                if ("protect".equals(o.kind) && !startKeys.contains(o.target)) badProtect++;
            }
            for (com.xjzb.rts.core.Mission.Event e : m.events) {
                if (!actions.contains(e.action)) badKind++;
                if (e.units != null)
                    for (String u : e.units)
                        if (!com.xjzb.rts.core.Game.TYPES.containsKey(u)) unknownUnits++;
                for (float[] pt : new float[][]{e.from, e.to})
                    if (pt != null && (pt[0] < 0 || pt[1] < 0
                            || pt[0] >= mw * 32 || pt[1] >= mh * 32)) offMap++;
            }
            for (String[] w : m.aiWaves)
                for (String u : w)
                    if (!com.xjzb.rts.core.Game.TYPES.containsKey(u)) unknownUnits++;

            // #9: the economy flag really does rebuild the map's mineral rows
            if (m.economy) {
                com.xjzb.rts.core.Game g = missionGame(id);
                if (g.minerals.isEmpty()) ecoMiss++;
            }
        }

        ok &= n >= 15 && indexMismatch == 0 && badMap == 0 && badRace == 0
                && unknownUnits == 0 && badKind == 0 && noEnemyHall == 0
                && noPlayerHall == 0 && badProtect == 0 && offMap == 0
                && blocked == 0 && ecoMiss == 0;
        sb.append(" missions=").append(n)
          .append(" index=").append(indexMismatch)
          .append(" map=").append(badMap)
          .append(" race=").append(badRace)
          .append(" unit=").append(unknownUnits)
          .append(" kind=").append(badKind)
          .append(" enemyHall=").append(noEnemyHall)
          .append(" playerHall=").append(noPlayerHall)
          .append(" protect=").append(badProtect)
          .append(" offMap=").append(offMap)
          .append(" blocked=").append(blocked)
          .append(" economy=").append(ecoMiss);
        System.out.println("  campaign walk" + sb + " PASS=" + ok);
    }

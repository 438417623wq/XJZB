/** v2.29 smoke walk: play every mission headless for 6 minutes and report the
 * board, so a level that loses on frame 1 or fields a mute enemy is visible. */
public class _V229Smoke {
    public static void main(String[] a) throws Exception {
        GameDesktop.readManifestPublic();
        java.util.List<String> ids = new java.util.ArrayList<>();
        for (String line : java.nio.file.Files.readAllLines(java.nio.file.Paths.get(
                GameDesktop.ASSETS + "/missions/index.txt"))) {
            String[] f = line.trim().split("\\|");
            if (f.length >= 3) ids.add(f[0]);
        }
        System.out.printf("%-5s %-14s %-8s %-4s %-24s %s%n",
                "id", "map", "race", "min", "at 60s (p vs e)", "at 360s");
        for (String id : ids) {
            com.xjzb.rts.core.Game g = GameDesktop.missionGame(id);
            String race = g.race;
            int min = g.minerals.size();
            String s60 = "", s360 = "";
            for (int t = 0; t < 30 * 360; t++) {
                g.update(1f / 30f);
                if (t == 30 * 60 - 1) s60 = tally(g);
                if (t == 30 * 360 - 1) s360 = tally(g);
                if (g.mission.finished) break;
            }
            String tail = g.mission.finished
                    ? ("  [" + (g.mission.victory ? "WIN" : "LOSE")
                       + " t=" + (int) g.mission.elapsed() + "]")
                    : "";
            System.out.printf("%-5s %-14s %-8s %-4d %-24s %s%s%n", id, g.mission.map,
                    race, min, s60, s360, tail);
        }
    }

    static String tally(com.xjzb.rts.core.Game g) {
        int pu = 0, pb = 0, eu = 0, eb = 0;
        for (com.xjzb.rts.core.Game.Ent e : g.ents) {
            if (!e.alive()) continue;
            if (e.team == 0) { if (e.isBuilding()) pb++; else pu++; }
            else { if (e.isBuilding()) eb++; else eu++; }
        }
        return pu + "u/" + pb + "b vs " + eu + "u/" + eb + "b";
    }
}

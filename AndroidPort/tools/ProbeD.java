import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * Batch D regression probe: GameDesktop run5 (the first run on the CORRECTED
 * terrain) ends with the player wiped -- 0 units, and then crashes at
 * GameDesktop.java:105 because there is no SCV left to order around.
 *
 * run4 predates the map regeneration, so the "52 PASS after the terrain fix"
 * claim was never actually re-verified. This prints the player's economy over
 * time to tell a real gameplay regression from ordinary AI pressure.
 */
public class ProbeD {
    static int mapW = 64, mapH = 64;
    static boolean[] walk;
    static List<int[]> starts = new ArrayList<>();
    static List<Object[]> units = new ArrayList<>();

    static final String ASSETS = "F:/KF/XJZB/AndroidPort/app/app/src/main/assets";

    static void readMap(String mapId) throws Exception {
        for (String line : Files.readAllLines(Paths.get(ASSETS + "/maps/" + mapId + "/meta.txt"))) {
            line = line.trim();
            if (line.startsWith("w=")) mapW = Integer.parseInt(line.substring(2));
            else if (line.startsWith("h=")) mapH = Integer.parseInt(line.substring(2));
            else if (line.startsWith("start=")) {
                String[] p = line.substring(6).split(",");
                starts.add(new int[]{Integer.parseInt(p[0]), Integer.parseInt(p[1])});
            } else if (line.startsWith("unit=")) {
                String[] p = line.substring(5).split(",");
                units.add(new Object[]{Integer.parseInt(p[0]),
                        Float.parseFloat(p[1]), Float.parseFloat(p[2]),
                        Integer.parseInt(p.length > 5 ? p[5] : "0")});
            }
        }
        walk = new boolean[mapW * 4 * mapH * 4];
        byte[] raw = null;
        for (String name : new String[]{"walk.bin.gz", "walk.gz", "walk.bin"}) {
            java.nio.file.Path p = Paths.get(ASSETS + "/maps/" + mapId + "/" + name);
            if (Files.exists(p)) {
                java.io.InputStream in = name.endsWith(".gz")
                        ? new java.util.zip.GZIPInputStream(Files.newInputStream(p))
                        : Files.newInputStream(p);
                raw = in.readAllBytes();
                in.close();
                break;
            }
        }
        if (raw != null)
            for (int i = 0; i < raw.length && i < walk.length; i++) walk[i] = raw[i] != 0;
        else java.util.Arrays.fill(walk, true);
    }

    public static void main(String[] args) throws Exception {
        readMap(args.length > 0 ? args[0] : "bloodbath");
        com.xjzb.rts.core.Game g = new com.xjzb.rts.core.Game(mapW, mapH, walk, starts, units);
        int scv0 = 0, mine0 = 0, bld0 = 0;
        for (com.xjzb.rts.core.Game.Ent e : g.ents) {
            if (e.team == 0) {
                if (e.isBuilding()) bld0++;
                else scv0++;
            }
        }
        System.out.println("t=0   player units=" + scv0 + " bldg=" + bld0);

        for (int sec = 1; sec <= 300; sec++) {
            for (int i = 0; i < 30; i++) g.update(1f / 30f);
            if (sec % 15 != 0) continue;
            int pu = 0, pb = 0, eu = 0, eb = 0;
            for (com.xjzb.rts.core.Game.Ent e : g.ents) {
                if (!e.alive()) continue;
                if (e.team == 0) { if (e.isBuilding()) pb++; else pu++; }
                else { if (e.isBuilding()) eb++; else eu++; }
            }
            System.out.printf("t=%-4d player %2d/%d  enemy %2d/%d  min=%5d gas=%4d sup=%d/%d status=%s%n",
                    sec, pu, pb, eu, eb, g.mineralsPlayer, g.gasPlayer,
                    g.supplyUsed, g.supplyCap, g.status);
            if (!g.status.isEmpty()) break;
        }
    }
}

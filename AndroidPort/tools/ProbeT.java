import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * Batch D regression probe 5: mining works now but the player loses every SCV
 * before the 180 s checkpoint (run4 with frozen SCVs had 4 alive). Dump the
 * mineral field around the player start and track SCV deaths to see whether
 * the workers are walking into the enemy or being shelled at home.
 */
public class ProbeT {
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
        for (String name : new String[]{"walk.bin.gz", "walk.gz", "walk.bin"}) {
            java.nio.file.Path p = Paths.get(ASSETS + "/maps/" + mapId + "/" + name);
            if (Files.exists(p)) {
                java.io.InputStream in = name.endsWith(".gz")
                        ? new java.util.zip.GZIPInputStream(Files.newInputStream(p))
                        : Files.newInputStream(p);
                byte[] raw = in.readAllBytes();
                in.close();
                for (int i = 0; i < raw.length && i < walk.length; i++) walk[i] = raw[i] != 0;
                break;
            }
        }
    }

    public static void main(String[] args) throws Exception {
        readMap(args.length > 0 ? args[0] : "bloodbath");
        com.xjzb.rts.core.Game g = new com.xjzb.rts.core.Game(mapW, mapH, walk, starts, units);

        System.out.println("starts: " + starts.size());
        for (int i = 0; i < starts.size(); i++)
            System.out.printf("  start%d px(%d,%d)%n", i, starts.get(i)[0], starts.get(i)[1]);

        com.xjzb.rts.core.Game.Ent cc = null;
        for (com.xjzb.rts.core.Game.Ent e : g.ents)
            if (e.team == 0 && e.isBuilding()) cc = e;
        System.out.printf("player first building: %s (%.0f,%.0f)%n", cc.type.key, cc.x, cc.y);

        System.out.println("minerals (sorted by distance to that building):");
        List<Object[]> ms = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Mineral m : g.minerals) {
            float d = (float) Math.sqrt((m.x - cc.x) * (m.x - cc.x) + (m.y - cc.y) * (m.y - cc.y));
            ms.add(new Object[]{d, m});
        }
        ms.sort((a, b) -> Float.compare((Float) a[0], (Float) b[0]));
        for (int i = 0; i < Math.min(10, ms.size()); i++) {
            com.xjzb.rts.core.Game.Mineral m = (com.xjzb.rts.core.Game.Mineral) ms.get(i)[1];
            System.out.printf("  d=%6.1f px(%4.0f,%4.0f) amt=%-5d %s%n",
                    ms.get(i)[0], m.x, m.y, m.amount, m.refinery != null ? "refinery" : "");
        }

        System.out.println("enemy units nearest to player base:");
        List<Object[]> es = new ArrayList<>();
        for (com.xjzb.rts.core.Game.Ent e : g.ents) {
            if (e.team != 1 || !e.alive()) continue;
            float d = (float) Math.sqrt((e.x - cc.x) * (e.x - cc.x) + (e.y - cc.y) * (e.y - cc.y));
            es.add(new Object[]{d, e});
        }
        es.sort((a, b) -> Float.compare((Float) a[0], (Float) b[0]));
        for (int i = 0; i < Math.min(6, es.size()); i++) {
            com.xjzb.rts.core.Game.Ent e = (com.xjzb.rts.core.Game.Ent) es.get(i)[1];
            System.out.printf("  d=%6.1f %-10s px(%4.0f,%4.0f) hp=%d%n",
                    es.get(i)[0], e.type.key, e.x, e.y, e.hp);
        }

        System.out.println("SCV deaths:");
        int alive = 0;
        for (int t = 0; t < 200; t++) {
            for (int i = 0; i < 30; i++) g.update(1f / 30f);
            int n = 0;
            for (com.xjzb.rts.core.Game.Ent e : g.ents)
                if (e.team == 0 && e.alive() && e.type.key.equals("scv")) n++;
            if (n != alive) {
                System.out.printf("  t=%-4d scv=%d min=%d%n", t, n, g.mineralsPlayer);
                alive = n;
            }
            if (n == 0) break;
        }
    }
}

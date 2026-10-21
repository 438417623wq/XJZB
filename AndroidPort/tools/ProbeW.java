import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * Batch D regression probe: the player's SCVs never mine on the regenerated
 * terrain (minerals frozen at 432 for 240 s), even though _e19/_e20 show the
 * start region is 72% of the map and all 60 resources are inside it.
 *
 * So dump what the workers are actually doing: where they spawned, whether
 * that spot is walkable, and which worker state they sit in.
 */
public class ProbeW {
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

    /** the game's own terrain test, at 8px minitile resolution */
    static boolean passMini(int px, int py) {
        int mx = px / 8, my = py / 8;
        int mw = mapW * 4, mh = mapH * 4;
        if (mx < 0 || my < 0 || mx >= mw || my >= mh) return false;
        return walk[my * mw + mx];
    }

    public static void main(String[] args) throws Exception {
        readMap(args.length > 0 ? args[0] : "bloodbath");
        com.xjzb.rts.core.Game g = new com.xjzb.rts.core.Game(mapW, mapH, walk, starts, units);

        System.out.println("minerals on map: " + g.minerals.size());
        for (int i = 0; i < Math.min(6, g.minerals.size()); i++) {
            com.xjzb.rts.core.Game.Mineral m = g.minerals.get(i);
            System.out.printf("  mineral%d (%6.1f,%6.1f) amt=%d%n", i, m.x, m.y, m.amount);
        }
        System.out.println("-- player workers at t=0 --");
        for (com.xjzb.rts.core.Game.Ent e : g.ents) {
            if (e.team != 0 || e.isBuilding()) continue;
            System.out.printf("  %-8s (%6.1f,%6.1f) walk=%s state=%d%n",
                    e.type.key, e.x, e.y, passMini((int) e.x, (int) e.y), e.workerState);
        }

        for (int sec = 1; sec <= 60; sec++) {
            for (int i = 0; i < 30; i++) g.update(1f / 30f);
            if (sec % 10 != 0) continue;
            System.out.println("-- t=" + sec + "s  minerals=" + g.mineralsPlayer + " --");
            int n = 0;
            for (com.xjzb.rts.core.Game.Ent e : g.ents) {
                if (e.team != 0 || e.isBuilding() || !e.alive()) continue;
                System.out.printf("  %-8s (%6.1f,%6.1f) walk=%s state=%d carry=%d moving=%s mineTgt=%s%n",
                        e.type.key, e.x, e.y, passMini((int) e.x, (int) e.y),
                        e.workerState, e.carrying,
                        e.moving, e.mineTarget == null ? "null" : "set");
                if (++n >= 4) break;
            }
        }
    }
}

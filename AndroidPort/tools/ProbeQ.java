import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * Batch D regression probe 2: the four SCVs returning to the command center
 * park at y~330 px and never reach the drop-off at y=268. Dump the full path
 * the follower is committed to plus the minitile walkability of the corridor
 * between the stuck point and the goal, to decide whether the new terrain
 * walls them in or the follower simply deadlocks in open ground.
 */
public class ProbeQ {
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

    static boolean mini(int mx, int my) {
        int mw = mapW * 4, mh = mapH * 4;
        if (mx < 0 || my < 0 || mx >= mw || my >= mh) return false;
        return walk[my * mw + mx];
    }

    public static void main(String[] args) throws Exception {
        readMap(args.length > 0 ? args[0] : "bloodbath");
        com.xjzb.rts.core.Game g = new com.xjzb.rts.core.Game(mapW, mapH, walk, starts, units);
        for (int i = 0; i < 40 * 30; i++) g.update(1f / 30f);

        // ASCII walkability, minitile x 10..26 / y 28..46  ('#' blocked)
        System.out.println("minitile map  x=10..26 (px 80..208)   y=28..46 (px 224..368)");
        System.out.print("      ");
        for (int mx = 10; mx <= 26; mx++) System.out.print((mx / 10) % 10);
        System.out.println();
        System.out.print("      ");
        for (int mx = 10; mx <= 26; mx++) System.out.print(mx % 10);
        System.out.println();
        for (int my = 28; my <= 46; my++) {
            System.out.printf("y%-4d ", my);
            for (int mx = 10; mx <= 26; mx++) System.out.print(mini(mx, my) ? '.' : '#');
            System.out.println();
        }
        System.out.println("cc minitiles = " + (144 / 8) + ".." + ((144 + 64) / 8)
                + " , " + (208 / 8) + ".." + ((208 + 64) / 8));

        for (com.xjzb.rts.core.Game.Ent e : g.ents) {
            if (e.team != 0 || e.isBuilding()) continue;
            System.out.printf("%n%s (%.1f,%.1f) st=%d idx=%d/%d goal=(%.0f,%.0f) mtile=(%.0f,%.0f)%n",
                    e.type.key, e.x, e.y, e.workerState, e.pathIndex, e.path.size(),
                    e.goalX, e.goalY, e.x / 8, e.y / 8);
            System.out.print("  path:");
            for (int i = 0; i < e.path.size(); i++) {
                int[] n = e.path.get(i);
                System.out.printf(" %d:(%d,%d)%s", i, n[0], n[1],
                        mini(n[0], n[1]) ? "" : "!BLOCKED");
            }
            System.out.println();
        }
    }
}

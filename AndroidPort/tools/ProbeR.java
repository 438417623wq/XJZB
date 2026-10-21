import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * Batch D regression probe 3: ProbeQ showed the corridor is fully walkable and
 * every committed path node is legal, yet the SCVs freeze. Step frame by frame
 * after the freeze and print x/y/pathIndex to see whether the follower is
 * truly pinned or merely oscillating inside one minitile.
 */
public class ProbeR {
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
        for (int i = 0; i < 40 * 30; i++) g.update(1f / 30f);

        com.xjzb.rts.core.Game.Ent w = null;
        for (com.xjzb.rts.core.Game.Ent e : g.ents)
            if (e.team == 0 && !e.isBuilding()) { w = e; break; }
        System.out.println("scv speed=" + w.type.speed + " radius=" + w.type.radius
                + " step@1/30=" + (w.type.speed / 30f));
        System.out.println("frame        x        y   idx  d(node)   target   time  status");
        for (int f = 0; f < 20; f++) {
            String node = "-";
            float d = -1;
            if (w.pathIndex < w.path.size()) {
                int[] n = w.path.get(w.pathIndex);
                float nx = n[0] * 8 + 4, ny = n[1] * 8 + 4;
                d = (float) Math.sqrt((nx - w.x) * (nx - w.x) + (ny - w.y) * (ny - w.y));
                node = String.format("(%d,%d)", n[0], n[1]);
            }
            System.out.printf("%5d %8.3f %8.3f %5d %8.3f   %s  %.1f  %s%n",
                    f, w.x, w.y, w.pathIndex, d, node, g.time, g.status);
            g.update(1f / 30f);
        }
    }
}

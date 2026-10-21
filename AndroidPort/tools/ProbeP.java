import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * Batch D regression probe: the SCVs mine once (400 -> 424 by t=10 s) then
 * freeze solid from t=20 s onward -- moving=true, position never changing.
 * Dump the path-follower state to find the equilibrium that traps them.
 */
public class ProbeP {
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

    static boolean passMini(int px, int py) {
        int mx = px / 8, my = py / 8;
        int mw = mapW * 4, mh = mapH * 4;
        if (mx < 0 || my < 0 || mx >= mw || my >= mh) return false;
        return walk[my * mw + mx];
    }

    public static void main(String[] args) throws Exception {
        readMap(args.length > 0 ? args[0] : "bloodbath");
        com.xjzb.rts.core.Game g = new com.xjzb.rts.core.Game(mapW, mapH, walk, starts, units);
        for (int i = 0; i < 40 * 30; i++) g.update(1f / 30f);

        System.out.println("player buildings:");
        for (com.xjzb.rts.core.Game.Ent e : g.ents) {
            if (e.team == 0 && e.isBuilding())
                System.out.printf("  %-12s (%6.1f,%6.1f) tiles=%d%n",
                        e.type.key, e.x, e.y, e.type.tiles);
        }
        System.out.println("workers at t=40s:");
        for (com.xjzb.rts.core.Game.Ent e : g.ents) {
            if (e.team != 0 || e.isBuilding()) continue;
            String node = "none";
            if (e.pathIndex < e.path.size()) {
                int[] n = e.path.get(e.pathIndex);
                node = String.format("(%d,%d)px(%d,%d)", n[0], n[1], n[0] * 8 + 4, n[1] * 8 + 4);
            }
            System.out.printf("  %-6s (%6.1f,%6.1f) st=%d moving=%s path=%d/%d idx=%d node=%s goal=(%.0f,%.0f)%n",
                    e.type.key, e.x, e.y, e.workerState, e.moving,
                    e.pathIndex, e.path.size(), e.pathIndex, node, e.goalX, e.goalY);
            if (e.mineTarget != null)
                System.out.printf("         mineTarget=(%.0f,%.0f) amt=%d%n",
                        e.mineTarget.x, e.mineTarget.y, e.mineTarget.amount);
        }
    }
}

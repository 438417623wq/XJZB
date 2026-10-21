import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * Batch D regression probe 7: the AI attack wave now reaches the player base
 * (it never did with the broken walk map). Confirm the arrivals walked there
 * legitimately -- every enemy inside 400 px of the player start must be
 * standing on walkable ground.
 */
public class ProbeV {
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
        float hx = starts.get(0)[0], hy = starts.get(0)[1];

        for (int t = 0; t < 115; t++)
            for (int i = 0; i < 30; i++) g.update(1f / 30f);

        int onWalk = 0, offWalk = 0;
        System.out.println("enemy units within 400 px of player start at t=115:");
        for (com.xjzb.rts.core.Game.Ent e : g.ents) {
            if (e.team != 1 || !e.alive() || e.isBuilding()) continue;
            float d = (float) Math.sqrt((e.x - hx) * (e.x - hx) + (e.y - hy) * (e.y - hy));
            if (d > 400) continue;
            int mx = (int) (e.x / 8), my = (int) (e.y / 8);
            boolean w = g.passMini(mx, my);
            if (w) onWalk++; else offWalk++;
            System.out.printf("  %-10s px(%4.0f,%4.0f) d=%3.0f mini(%d,%d) walkable=%s%n",
                    e.type.key, e.x, e.y, d, mx, my, w);
        }
        System.out.println("onWalkable=" + onWalk + " offWalkable=" + offWalk);
    }
}

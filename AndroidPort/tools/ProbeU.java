import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * Batch D regression probe 6: SCVs die one at a time at t=160/163/166/169 with
 * the nearest enemy 1344 px away at t=0. Track enemy units converging on the
 * player base and the SCVs' hp/position, to decide whether the fixed terrain
 * simply lets the AI reach the player for the first time.
 */
public class ProbeU {
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

        for (int t = 0; t <= 180; t++) {
            if (t % 10 == 0 || (t >= 155 && t <= 175)) {
                int near = 0, scv = 0, pb = 0;
                float best = 9e9f;
                String bestKey = "";
                for (com.xjzb.rts.core.Game.Ent e : g.ents) {
                    if (!e.alive()) continue;
                    if (e.team == 1 && !e.isBuilding()) {
                        float d = (float) Math.sqrt((e.x - hx) * (e.x - hx) + (e.y - hy) * (e.y - hy));
                        if (d < 400) near++;
                        if (d < best) { best = d; bestKey = e.type.key; }
                    }
                    if (e.team == 0 && e.type.key.equals("scv")) scv++;
                    if (e.team == 0 && e.isBuilding()) pb++;
                }
                StringBuilder sb = new StringBuilder();
                for (com.xjzb.rts.core.Game.Ent e : g.ents)
                    if (e.team == 0 && e.alive() && e.type.key.equals("scv"))
                        sb.append(String.format("[%d@(%.0f,%.0f)]", e.hp, e.x, e.y));
                System.out.printf("t=%-4d scv=%d bldg=%d min=%-5d nearEnemy=%d closest=%.0f(%s) %s%n",
                        t, scv, pb, g.mineralsPlayer, near, best, bestKey, sb);
            }
            for (int i = 0; i < 30; i++) g.update(1f / 30f);
        }
    }
}

import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * Batch D regression probe 4: is the worker freeze caused by worker-vs-worker
 * separation (a 4-way equilibrium) or by something global? Run the same map
 * three ways and compare the mineral curve.
 */
public class ProbeS {
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

    static com.xjzb.rts.core.Game fresh() {
        return new com.xjzb.rts.core.Game(mapW, mapH, walk, starts, units);
    }

    static int playerUnits(com.xjzb.rts.core.Game g) {
        int n = 0;
        for (com.xjzb.rts.core.Game.Ent e : g.ents)
            if (e.team == 0 && !e.isBuilding() && e.alive()) n++;
        return n;
    }

    static void run(String label, int keep) {
        com.xjzb.rts.core.Game g = fresh();
        for (int i = 0; i < 40 * 30; i++) g.update(1f / 30f);
        // delete all but `keep` workers, scattering the survivors far apart
        int dropped = 0;
        for (com.xjzb.rts.core.Game.Ent e : g.ents) {
            if (e.team != 0 || e.isBuilding()) continue;
            if (dropped < 4 - keep) {
                e.hp = 0;
                dropped++;
            } else if (dropped > 0) {
                e.x = 900 + dropped * 40;
                e.y = 900;
                e.moving = false;
                e.path.clear();
                e.workerState = 0;
            }
        }
        StringBuilder sb = new StringBuilder();
        int last = -1;
        for (int t = 0; t < 240; t++) {
            for (int i = 0; i < 30; i++) g.update(1f / 30f);
            if (t % 20 == 0 || g.mineralsPlayer != last) {
                if (t % 20 == 0) {
                    sb.append(String.format("  t=%-4d min=%-5d units=%d%n", t, g.mineralsPlayer, playerUnits(g)));
                    last = g.mineralsPlayer;
                }
            }
        }
        System.out.printf("%s:%n%s", label, sb);
    }

    public static void main(String[] args) throws Exception {
        readMap(args.length > 0 ? args[0] : "bloodbath");
        run("all 4 workers", 4);
        run("1 worker only", 1);
    }
}


import com.xjzb.rts.core.Game;
import java.io.File;
import java.nio.file.*;
import java.util.*;

public class ReplayGen {
    static String ASSETS = "F:/KF/XJZB/AndroidPort/app/app/src/main/assets";
    static int mapW, mapH;
    static boolean[] walk;
    static List<int[]> starts = new ArrayList<>();
    static List<Object[]> units = new ArrayList<>();

    public static void main(String[] a) throws Exception {
        String id = a.length > 0 ? a[0] : "bloodbath";
        String name = a.length > 1 ? a[1] : "bloodbath_demo";
        String race = a.length > 2 ? a[2] : "terran";
        load(id);
        String worker = "zerg".equals(race) ? "drone" : ("protoss".equals(race) ? "probe" : "scv");
        String supply = "zerg".equals(race) ? "pool" : ("protoss".equals(race) ? "pylon" : "depot");

        Game g = new Game(mapW, mapH, walk, starts, units, race);
        g.recording = true; g.mapId = id; g.difficulty = 1;
        List<Game.Ent> ws = workers(g, worker);
        System.out.println("workers=" + ws.size() + " minerals=" + g.minerals.size());

        // 1. mine
        for (int t = 0; t < 60; t++) g.update(1f/30f);
        if (!ws.isEmpty() && !g.minerals.isEmpty()) {
            Game.Mineral m = g.minerals.get(0);
            g.orderHarvest(ws, m);
            g.recordOrder("harvest", ws, String.valueOf(g.minerals.indexOf(m)));
        }
        for (int t = 0; t < 60*40; t++) g.update(1f/30f);

        // 2. build supply next to the base (findBuildSpot mirrors the harness)
        if (!ws.isEmpty()) {
            Game.Ent w0 = ws.get(0);
            float[] spot = findBuildSpot(g, w0, supply);
            if (spot != null) {
                boolean ok = g.tryBuild(w0, supply, spot[0], spot[1]);
                g.recordOrder("build", ws.subList(0,1), supply + " " + spot[0] + " " + spot[1]);
                System.out.println("build " + supply + "=" + ok + " minerals=" + g.mineralsPlayer);
            } else System.out.println("no build spot for " + supply);
        }
        for (int t = 0; t < 60*30; t++) g.update(1f/30f);

        // 3. re-target the workers onto the patch nearest the new building,
        //    then (when the race has any army) push it at the enemy base
        List<Game.Ent> ws2 = workers(g, worker);
        Game.Mineral best = null; float bd = Float.MAX_VALUE;
        if (!ws2.isEmpty() && !g.minerals.isEmpty()) {
            float wx = ws2.get(0).x, wy = ws2.get(0).y;
            for (Game.Mineral m : g.minerals) {
                if (m.amount <= 0) continue;
                float d = (m.x-wx)*(m.x-wx) + (m.y-wy)*(m.y-wy);
                if (d < bd) { bd = d; best = m; }
            }
            if (best != null) { g.orderHarvest(ws2, best);
                g.recordOrder("harvest", ws2, String.valueOf(g.minerals.indexOf(best))); }
        }
        for (int t = 0; t < 60*25; t++) g.update(1f/30f);
        List<Game.Ent> army = army(g, worker);
        float[] eb = g.findEnemyBase();
        if (!army.isEmpty()) { g.orderMove(army, eb[0], eb[1], true);
            g.recordOrder("move", army, eb[0] + " " + eb[1] + " 1"); }
        else { g.orderMove(ws2, eb[0], eb[1], false);
            g.recordOrder("move", ws2, eb[0] + " " + eb[1]); }
        for (int t = 0; t < 60*35; t++) g.update(1f/30f);

        String rep = g.serializeReplay();
        System.out.println("cmds=" + g.replayLog.size() + " tick=" + g.tick);
        System.out.println(rep);
        File out = new File(ASSETS + "/replays/" + name + ".txt");
        out.getParentFile().mkdirs();
        Files.write(out.toPath(), rep.getBytes("UTF-8"));
        System.out.println("wrote " + out.getName() + " bytes=" + rep.length());
    }

    static float[] findBuildSpot(Game g, Game.Ent w, String key) {
        float[] dx = {80, -80, 80, -80, 160, -160, 0, 0};
        float[] dy = {80, 80, -80, -80, 0, 0, 160, -160};
        for (int i = 0; i < dx.length; i++) {
            float bx = w.x + dx[i], by = w.y + dy[i];
            if (g.buildError(key, bx, by) == null) return new float[]{bx, by};
        }
        return null;
    }
    static List<Game.Ent> workers(Game g, String key) {
        List<Game.Ent> out = new ArrayList<>();
        for (Game.Ent e : g.ents) if (e.team == 0 && e.type.key.equals(key)) out.add(e);
        return out;
    }
    static List<Game.Ent> army(Game g, String worker) {
        List<Game.Ent> out = new ArrayList<>();
        for (Game.Ent e : g.ents)
            if (e.team == 0 && !e.isBuilding() && !e.type.key.equals(worker)) out.add(e);
        return out;
    }
    static void load(String id) throws Exception {
        for (String line : Files.readAllLines(Paths.get(ASSETS + "/maps/" + id + "/meta.txt"))) {
            line = line.trim();
            if (line.startsWith("w=")) mapW = Integer.parseInt(line.substring(2));
            else if (line.startsWith("h=")) mapH = Integer.parseInt(line.substring(2));
            else if (line.startsWith("start=")) { String[] p=line.substring(6).split(",");
                starts.add(new int[]{Integer.parseInt(p[0]), Integer.parseInt(p[1])}); }
            else if (line.startsWith("unit=")) { String[] p=line.substring(5).split(",");
                units.add(new Object[]{Integer.parseInt(p[0]), Float.parseFloat(p[1]),
                    Float.parseFloat(p[2]), Integer.parseInt(p.length>5?p[5]:"0")}); }
        }
        walk = new boolean[mapW*4*mapH*4];
        for (String n : new String[]{"walk.bin.gz","walk.gz","walk.bin"}) {
            Path pp = Paths.get(ASSETS + "/maps/" + id + "/" + n);
            if (Files.exists(pp)) {
                java.io.InputStream in = n.endsWith(".gz")
                    ? new java.util.zip.GZIPInputStream(Files.newInputStream(pp)) : Files.newInputStream(pp);
                byte[] raw = in.readAllBytes(); in.close();
                for (int i=0;i<raw.length && i<walk.length;i++) walk[i]=raw[i]!=0;
                break;
            }
        }
    }
}

import java.util.*;
public class _Dbg236b {
    /** 8-connected flood with a 1-cell dilation, matching pipeline_maps.py's
     * start-connectivity gate -- the project's own definition of "playable". */
    static boolean[] reach(com.xjzb.rts.core.Game g, int sx, int sy) {
        int w = g.wMini, h = g.hMini;
        // dilate: a minitile is usable if it or any 8-neighbour walks
        boolean[] ok = new boolean[w * h];
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++) {
                if (g.passMini(x, y)) { ok[y * w + x] = true; continue; }
                for (int dy = -1; dy <= 1 && !ok[y * w + x]; dy++)
                    for (int dx = -1; dx <= 1; dx++) {
                        int X = x + dx, Y = y + dy;
                        if (X < 0 || Y < 0 || X >= w || Y >= h) continue;
                        if (g.passMini(X, Y)) { ok[y * w + x] = true; break; }
                    }
            }
        int[] st = g.nearestPassMini(sx, sy, 40);
        if (st == null) return null;
        boolean[] seen = new boolean[w * h];
        ArrayDeque<int[]> q = new ArrayDeque<>();
        q.add(st); seen[st[1] * w + st[0]] = true;
        int[][] D = {{1,0},{-1,0},{0,1},{0,-1},{1,1},{1,-1},{-1,1},{-1,-1}};
        while (!q.isEmpty()) {
            int[] p = q.poll();
            for (int[] d : D) {
                int X = p[0] + d[0], Y = p[1] + d[1];
                if (X < 0 || Y < 0 || X >= w || Y >= h) continue;
                if (seen[Y * w + X] || !ok[Y * w + X]) continue;
                seen[Y * w + X] = true; q.add(new int[]{X, Y});
            }
        }
        return seen;
    }

    public static void main(String[] a) throws Exception {
        GameDesktop.readManifestPublic();
        for (String line : java.nio.file.Files.readAllLines(java.nio.file.Paths.get(
                GameDesktop.ASSETS + "/missions/index.txt"))) {
            String[] f = line.trim().split("\\|");
            if (f.length < 3) continue;
            String id = f[0];
            com.xjzb.rts.core.Game g = GameDesktop.missionGame(id);
            com.xjzb.rts.core.Game.Ent hall = null;
            for (com.xjzb.rts.core.Game.Ent e : g.ents)
                if (e.team == 0 && hall == null && ("cc".equals(e.type.key)
                        || "hatchery".equals(e.type.key) || "nexus".equals(e.type.key))) hall = e;
            boolean destroy = false;
            for (com.xjzb.rts.core.Mission.Objective o : g.mission.objectives)
                if ("destroyAll".equals(o.kind)) destroy = true;
            boolean[] seen = reach(g, (int) (hall.x / 8), (int) (hall.y / 8));
            int total = 0, hit = 0;
            StringBuilder unreach = new StringBuilder();
            for (com.xjzb.rts.core.Game.Ent e : g.ents) {
                if (e.team != 1 || !"hatchery".equals(e.type.key)) continue;
                total++;
                // The hatchery's own tile is blocked by its footprint, so ask
                // for the nearest walkable tile rather than testing the tile it
                // stands on -- otherwise every level looks unreachable.
                int[] fs = g.nearestPassMini((int) (e.x / 8), (int) (e.y / 8), 40);
                if (fs != null && seen[fs[1] * g.wMini + fs[0]]) hit++;
                else unreach.append(" (").append(fs == null ? "null" : fs[0] + "," + fs[1]).append(")");
            }
            System.out.println(id + " destroyAll=" + destroy + " halls=" + total
                    + " reachable=" + hit
                    + (unreach.length() > 0 ? " UNREACH:" + unreach : ""));
        }
    }
}
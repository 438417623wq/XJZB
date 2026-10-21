import java.util.*;
public class _Dbg236d {
    public static void main(String[] a) throws Exception {
        GameDesktop.readManifestPublic();
        for (String id : new String[]{"m05","m15","m01"}) {
            com.xjzb.rts.core.Game g = GameDesktop.missionGame(id);
            int w = g.wMini, h = g.hMini;
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
            int[] lab = new int[w * h];
            int comp = 0; int[] sizes = new int[200];
            int[][] D = {{1,0},{-1,0},{0,1},{0,-1},{1,1},{1,-1},{-1,1},{-1,-1}};
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++) {
                    if (!ok[y * w + x] || lab[y * w + x] != 0) continue;
                    comp++;
                    ArrayDeque<int[]> q = new ArrayDeque<>();
                    q.add(new int[]{x, y}); lab[y * w + x] = comp;
                    int n = 0;
                    while (!q.isEmpty()) {
                        int[] p = q.poll(); n++;
                        for (int[] d : D) {
                            int X = p[0] + d[0], Y = p[1] + d[1];
                            if (X < 0 || Y < 0 || X >= w || Y >= h) continue;
                            if (lab[Y * w + X] != 0 || !ok[Y * w + X]) continue;
                            lab[Y * w + X] = comp; q.add(new int[]{X, Y});
                        }
                    }
                    sizes[comp] = n;
                }
            com.xjzb.rts.core.Game.Ent hall = null;
            for (com.xjzb.rts.core.Game.Ent e : g.ents)
                if (e.team == 0 && hall == null && ("cc".equals(e.type.key)
                        || "hatchery".equals(e.type.key) || "nexus".equals(e.type.key))) hall = e;
            int[] hs = g.nearestPassMini((int) (hall.x / 8), (int) (hall.y / 8), 40);
            int hc = lab[hs[1] * w + hs[0]];
            StringBuilder sb = new StringBuilder();
            for (com.xjzb.rts.core.Game.Ent e : g.ents) {
                if (e.team != 1 || !"hatchery".equals(e.type.key)) continue;
                int[] fs = g.nearestPassMini((int) (e.x / 8), (int) (e.y / 8), 40);
                int fc = fs == null ? -1 : lab[fs[1] * w + fs[0]];
                sb.append(" foe@").append((int) e.x).append(",").append((int) e.y)
                  .append("->comp").append(fc).append("(size").append(fc > 0 ? sizes[fc] : -1).append(")")
                  .append(fc == hc ? " OK" : " UNREACHABLE");
            }
            System.out.println(id + " comps=" + comp + " playerHallComp=" + hc
                    + "(size" + sizes[hc] + ")" + sb);
        }
    }
}
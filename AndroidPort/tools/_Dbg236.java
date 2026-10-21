import java.util.*;
public class _Dbg236 {
    public static void main(String[] a) throws Exception {
        GameDesktop.readManifestPublic();
        for (String id : new String[]{"m01", "m05", "m06", "m15"}) {
            com.xjzb.rts.core.Game g = GameDesktop.missionGame(id);
            com.xjzb.rts.core.Game.Ent hall = null, foe = null;
            for (com.xjzb.rts.core.Game.Ent e : g.ents) {
                if (e.team == 0 && hall == null && ("cc".equals(e.type.key)
                        || "hatchery".equals(e.type.key) || "nexus".equals(e.type.key))) hall = e;
                if (e.team == 1 && "hatchery".equals(e.type.key) && foe == null) foe = e;
            }
            int hx = (int) (hall.x / 8), hy = (int) (hall.y / 8);
            int fx = (int) (foe.x / 8), fy = (int) (foe.y / 8);
            System.out.println(id + " hall=" + hx + "," + hy + " foe=" + fx + "," + fy
                    + " passHall=" + g.passMini(hx, hy) + " passFoe=" + g.passMini(fx, fy));
            // flood fill from a walkable tile beside the player's hall
            int[] st = g.nearestPassMini(hx, hy, 40);
            System.out.println("   nearestPass(hall)=" + (st == null ? "null" : st[0] + "," + st[1]));
            boolean[] seen = new boolean[g.wMini * g.hMini];
            ArrayDeque<int[]> q = new ArrayDeque<>();
            q.add(st); seen[st[1] * g.wMini + st[0]] = true;
            int n = 0;
            while (!q.isEmpty()) {
                int[] p = q.poll(); n++;
                for (int[] d : new int[][]{{1,0},{-1,0},{0,1},{0,-1}}) {
                    int X = p[0] + d[0], Y = p[1] + d[1];
                    if (X < 0 || Y < 0 || X >= g.wMini || Y >= g.hMini) continue;
                    if (seen[Y * g.wMini + X] || !g.passMini(X, Y)) continue;
                    seen[Y * g.wMini + X] = true; q.add(new int[]{X, Y});
                }
            }
            int[] fs = g.nearestPassMini(fx, fy, 40);
            boolean foeInFlood = fs != null && seen[fs[1] * g.wMini + fs[0]];
            System.out.println("   floodFromHall=" + n + " of " + (g.wMini * g.hMini)
                    + "  foeReachable=" + foeInFlood);
            List<int[]> p = g.findPath(hx, hy, fx, fy);
            System.out.println("   findPath len=" + (p == null ? "null" : p.size()));
        }
    }
}
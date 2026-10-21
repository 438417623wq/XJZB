import java.util.*;
public class _Dbg236e {
    public static void main(String[] a) throws Exception {
        GameDesktop.readManifestPublic();
        com.xjzb.rts.core.Game g = GameDesktop.missionGame("m05");
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
        int[][] D = {{1,0},{-1,0},{0,1},{0,-1},{1,1},{1,-1},{-1,1},{-1,-1}};
        int comp = 0;
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++) {
                if (!ok[y * w + x] || lab[y * w + x] != 0) continue;
                comp++;
                ArrayDeque<int[]> q = new ArrayDeque<>();
                q.add(new int[]{x, y}); lab[y * w + x] = comp;
                while (!q.isEmpty()) {
                    int[] p = q.poll();
                    for (int[] d : D) {
                        int X = p[0] + d[0], Y = p[1] + d[1];
                        if (X < 0 || Y < 0 || X >= w || Y >= h) continue;
                        if (lab[Y * w + X] != 0 || !ok[Y * w + X]) continue;
                        lab[Y * w + X] = comp; q.add(new int[]{X, Y});
                    }
                }
            }
        int hallComp = lab[(g.nearestPassMini(42, 22, 40)[1]) * w + g.nearestPassMini(42, 22, 40)[0]];
        System.out.println("player comp=" + hallComp);
        // for the target area (in 4-tile steps), find comp-hall spots with a
        // 5x5-tile clear patch, closest to the old outpost at (3152,3152)
        int bx = 3152, by = 3152;
        int best = Integer.MAX_VALUE; int[] bestSpot = null;
        for (int y = 8; y < h - 40; y++)
            for (int x = 8; x < w - 40; x++) {
                if (lab[y * w + x] != hallComp) continue;
                // require a 5x5-tile (20 minitile) clear block
                boolean clear = true;
                for (int dy = 0; dy < 20 && clear; dy += 4)
                    for (int dx = 0; dx < 20; dx += 4)
                        if (!g.passMini(x + dx, y + dy)) { clear = false; break; }
                if (!clear) continue;
                int px = (x + 10) * 8, py = (y + 10) * 8;
                int d = Math.abs(px - bx) + Math.abs(py - by);
                if (d < best) { best = d; bestSpot = new int[]{px, py}; }
            }
        System.out.println("closest reachable clear spot near outpost: "
                + (bestSpot == null ? "none" : bestSpot[0] + "," + bestSpot[1] + " dist=" + best));
        if (bestSpot != null) {
            // report the walkable neighbourhood so the base layout fits
            for (int y = bestSpot[1] / 8 - 12; y <= bestSpot[1] / 8 + 14; y += 4) {
                StringBuilder sb = new StringBuilder();
                for (int x = bestSpot[0] / 8 - 14; x <= bestSpot[0] / 8 + 14; x += 2)
                    sb.append((x < 0 || y < 0 || x >= w || y >= h) ? '?'
                            : (g.passMini(x, y) ? '#' : '.'));
                System.out.println("   " + (y * 8) + " " + sb);
            }
        }
    }
}
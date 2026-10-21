import java.util.*;
public class _Dbg236c {
    public static void main(String[] a) throws Exception {
        GameDesktop.readManifestPublic();
        GameDesktop.readMapPublic("hunters");
        com.xjzb.rts.core.Game g = new com.xjzb.rts.core.Game(
                GameDesktop.mapW, GameDesktop.mapH, GameDesktop.walk, GameDesktop.elev,
                GameDesktop.starts, GameDesktop.units, "terran");
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
        // label every connected component of `ok`
        int[] lab = new int[w * h];
        int comp = 0;
        int[][] D = {{1,0},{-1,0},{0,1},{0,-1},{1,1},{1,-1},{-1,1},{-1,-1}};
        int[] sizes = new int[64];
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
                if (comp < sizes.length) sizes[comp] = n;
            }
        System.out.println("hunters: " + comp + " components (dilated walk)");
        for (int i = 1; i <= Math.min(comp, 12); i++)
            System.out.println("   comp " + i + " size=" + sizes[i]);
        // which component holds each mission start and each m05 enemy base
        int[][] probes = {{336,176},{2368,240},{3200,3200},{384,3696},{3712,3760}};
        for (int[] p : probes) {
            int[] s = g.nearestPassMini(p[0] / 8, p[1] / 8, 40);
            System.out.println("   probe (" + p[0] + "," + p[1] + ") nearestPass="
                    + (s == null ? "null" : s[0] * 8 + "," + s[1] * 8)
                    + " -> comp " + (s == null ? -1 : lab[s[1] * w + s[0]]));
        }
        // coarse map: first digit of component id
        System.out.println("   coarse map ('#' = comp 1, '+' = comp 2, '-' = other, '.' = blocked)");
        for (int y = 0; y < h; y += 16) {
            StringBuilder sb = new StringBuilder();
            for (int x = 0; x < w; x += 16) {
                int c = lab[y * w + x];
                sb.append(c == 0 ? '.' : c == 1 ? '#' : c == 2 ? '+' : (c < 10 ? (char)('0' + c) : '*'));
            }
            System.out.println("   " + sb);
        }
    }
}
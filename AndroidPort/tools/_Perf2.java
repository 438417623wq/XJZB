/** Perf probe with real combat + pathfinding load. */
public class _Perf2 {
    public static void main(String[] a) throws Exception {
        Class<?> gd = Class.forName("GameDesktop");
        for (String m : new String[]{"readManifest", "readMap"}) {
            java.lang.reflect.Method x = gd.getDeclaredMethod(m); x.setAccessible(true); x.invoke(null);
        }
        int mapW = f(gd, "mapW"), mapH = f(gd, "mapH");
        boolean[] walk = (boolean[]) fld(gd, "walk");
        byte[] elev = (byte[]) fld(gd, "elev");
        java.util.List<int[]> starts = (java.util.List<int[]>) fld(gd, "starts");
        java.util.List<Object[]> units = (java.util.List<Object[]>) fld(gd, "units");
        for (int n : new int[]{60, 120, 200}) {
            com.xjzb.rts.core.Game g = new com.xjzb.rts.core.Game(mapW, mapH, walk, elev, starts, units, "terran");
            java.util.List<com.xjzb.rts.core.Game.Ent> drop = new java.util.ArrayList<>();
            for (com.xjzb.rts.core.Game.Ent e : g.ents) if (e.team != 0) drop.add(e);
            g.ents.removeAll(drop);
            g.supplyCap = 400;
            java.util.Random rnd = new java.util.Random(11);
            float cx = g.wPx * 0.35f, cy = g.hPx * 0.5f;
            java.util.List<com.xjzb.rts.core.Game.Ent> mine = new java.util.ArrayList<>();
            java.util.List<com.xjzb.rts.core.Game.Ent> foe = new java.util.ArrayList<>();
            for (int i = 0; i < n; i++) {
                mine.add(g.spawn("marine", 0, cx + rnd.nextFloat() * 160, cy + rnd.nextFloat() * 160, true));
                foe.add(g.spawn("zergling", 1, cx + 300 + rnd.nextFloat() * 160, cy + rnd.nextFloat() * 160, true));
            }
            int steps = 300;
            long t0 = System.nanoTime();
            for (int i = 0; i < steps; i++) {
                // re-issue attack-moves periodically so A* keeps running
                if (i % 30 == 0) {
                    g.orderMove(mine, cx + 300, cy, true);
                    g.orderMove(foe, cx, cy, true);
                }
                g.update(1f / 30f);
            }
            double perTick = (System.nanoTime() - t0) / 1e6 / steps;
            System.out.printf("  n=%-4d alive=%-4d %.3f ms/tick  %s%n",
                    n, g.ents.size(), perTick,
                    perTick < 8 ? "OK" : perTick < 16 ? "TIGHT" : "SLOW");
        }
    }
    static int f(Class<?> c, String n) throws Exception { java.lang.reflect.Field x = c.getDeclaredField(n); x.setAccessible(true); return x.getInt(null); }
    static Object fld(Class<?> c, String n) throws Exception { java.lang.reflect.Field x = c.getDeclaredField(n); x.setAccessible(true); return x.get(null); }
}
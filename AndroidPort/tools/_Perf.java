/** Perf probe: how does Game.update() scale with entity count? */
public class _Perf {
    static int mapW, mapH; static boolean[] walk; static byte[] elev;
    static java.util.List<int[]> starts; static java.util.List<Object[]> units;
    public static void main(String[] a) throws Exception {
        Class<?> gd = Class.forName("GameDesktop");
        for (String m : new String[]{"readManifest", "readMap"}) {
            java.lang.reflect.Method x = gd.getDeclaredMethod(m); x.setAccessible(true); x.invoke(null);
        }
        java.lang.reflect.Field fw = gd.getDeclaredField("mapW"); fw.setAccessible(true);
        java.lang.reflect.Field fh = gd.getDeclaredField("mapH"); fh.setAccessible(true);
        java.lang.reflect.Field fwalk = gd.getDeclaredField("walk"); fwalk.setAccessible(true);
        java.lang.reflect.Field felev = gd.getDeclaredField("elev"); felev.setAccessible(true);
        java.lang.reflect.Field fst = gd.getDeclaredField("starts"); fst.setAccessible(true);
        java.lang.reflect.Field fun = gd.getDeclaredField("units"); fun.setAccessible(true);
        mapW = fw.getInt(null); mapH = fh.getInt(null);
        walk = (boolean[]) fwalk.get(null); elev = (byte[]) felev.get(null);
        starts = (java.util.List<int[]>) fst.get(null);
        units = (java.util.List<Object[]>) fun.get(null);
        for (int n : new int[]{80, 160, 300}) {
            com.xjzb.rts.core.Game g = new com.xjzb.rts.core.Game(mapW, mapH, walk, elev, starts, units, "terran");
            java.util.List<com.xjzb.rts.core.Game.Ent> drop = new java.util.ArrayList<>();
            for (com.xjzb.rts.core.Game.Ent e : g.ents) if (e.team != 0) drop.add(e);
            g.ents.removeAll(drop);
            java.util.Random rnd = new java.util.Random(7);
            for (int i = 0; i < n; i++) {
                float x = 200 + rnd.nextFloat() * (g.wPx - 400);
                float y = 200 + rnd.nextFloat() * (g.hPx - 400);
                g.spawn(i % 3 == 0 ? "marine" : i % 3 == 1 ? "zergling" : "zealot",
                        i % 2, x, y, true);
            }
            // warm up
            for (int i = 0; i < 60; i++) g.update(1f / 30f);
            int steps = 600;
            long t0 = System.nanoTime();
            for (int i = 0; i < steps; i++) g.update(1f / 30f);
            long dt = System.nanoTime() - t0;
            double perTick = dt / 1e6 / steps;
            System.out.printf("  n=%-4d ents=%-4d %.3f ms/tick  budget@30fps=33.3ms  %s%n",
                    n, g.ents.size(), perTick, perTick < 8 ? "OK" : perTick < 16 ? "TIGHT" : "SLOW");
        }
    }
}
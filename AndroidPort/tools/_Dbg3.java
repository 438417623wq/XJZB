public class _Dbg3 {
    static int mapW, mapH; static boolean[] walk; static byte[] elev;
    static java.util.List<int[]> starts; static java.util.List<Object[]> units;
    public static void main(String[] a) throws Exception {
        Class<?> gd = Class.forName("GameDesktop");
        for (String m : new String[]{"readManifest", "readMap"}) {
            java.lang.reflect.Method x = gd.getDeclaredMethod(m);
            x.setAccessible(true); x.invoke(null);
        }
        mapW = f(gd, "mapW"); mapH = f(gd, "mapH");
        walk = (boolean[]) fld(gd, "walk"); elev = (byte[]) fld(gd, "elev");
        starts = (java.util.List<int[]>) fld(gd, "starts"); units = (java.util.List<Object[]>) fld(gd, "units");
        java.lang.reflect.Method cg = gd.getDeclaredMethod("cleanGame", String.class);
        cg.setAccessible(true);
        com.xjzb.rts.core.Game g = (com.xjzb.rts.core.Game) cg.invoke(null, "terran");
        g.mineralsPlayer = 5000; g.gasPlayer = 5000;
        java.lang.reflect.Method cgr = gd.getDeclaredMethod("clearGround", com.xjzb.rts.core.Game.class, int.class, int.class);
        cgr.setAccessible(true);
        float[] s2 = (float[]) cgr.invoke(null, g, 3, 4);
        System.out.println("spot=" + s2[0] + "," + s2[1] + " mapWpx=" + g.wPx + " mapHpx=" + g.hPx);
        com.xjzb.rts.core.Game.Ent sp = g.spawn("starport", 0, s2[0], s2[1], true);
        System.out.println("starport=" + (sp != null));
        System.out.println("supplyUsed=" + g.supplyUsed + " cap=" + g.supplyCap);
        System.out.println("trainError(wraith)=" + g.trainError("wraith"));
        System.out.println("trainError(dropship)=" + g.trainError("dropship"));
        System.out.println("trainError(valkyrie)=" + g.trainError("valkyrie"));
        System.out.println("addonError(controlt)=" + g.addonError(sp, "controlt"));
        com.xjzb.rts.core.Game.Ent tower = g.buildAddon(sp, "controlt");
        System.out.println("tower=" + tower);
        System.out.println("after: trainError(dropship)=" + g.trainError("dropship"));
    }
    static int f(Class<?> c, String n) throws Exception { java.lang.reflect.Field x = c.getDeclaredField(n); x.setAccessible(true); return x.getInt(null); }
    static Object fld(Class<?> c, String n) throws Exception { java.lang.reflect.Field x = c.getDeclaredField(n); x.setAccessible(true); return x.get(null); }
}
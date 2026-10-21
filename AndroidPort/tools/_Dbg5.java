public class _Dbg5 {
    static int mapW, mapH; static boolean[] walk; static byte[] elev;
    static java.util.List<int[]> starts; static java.util.List<Object[]> units;
    public static void main(String[] a) throws Exception {
        Class<?> gd = Class.forName("GameDesktop");
        for (String m : new String[]{"readManifest", "readMap"}) {
            java.lang.reflect.Method x = gd.getDeclaredMethod(m); x.setAccessible(true); x.invoke(null);
        }
        mapW = f(gd, "mapW"); mapH = f(gd, "mapH");
        walk = (boolean[]) fld(gd, "walk"); elev = (byte[]) fld(gd, "elev");
        starts = (java.util.List<int[]>) fld(gd, "starts"); units = (java.util.List<Object[]>) fld(gd, "units");
        java.lang.reflect.Method cg = gd.getDeclaredMethod("cleanGame", String.class); cg.setAccessible(true);
        com.xjzb.rts.core.Game g = (com.xjzb.rts.core.Game) cg.invoke(null, "terran");
        g.mineralsPlayer = 5000; g.gasPlayer = 5000; g.supplyCap = 200;
        java.lang.reflect.Method cgr = gd.getDeclaredMethod("clearGround", com.xjzb.rts.core.Game.class, int.class, int.class);
        cgr.setAccessible(true);
        float[] s4 = (float[]) cgr.invoke(null, g, 3, 4);
        com.xjzb.rts.core.Game.Ent sf = g.spawn("sciencefac", 0, s4[0], s4[1], true);
        com.xjzb.rts.core.Game.Ent silo = g.buildAddon(sf, "nukesilo");
        for (int i = 0; i < 905; i++) g.update(1f/30f);
        System.out.println("armed=" + silo.nukeArmed + " ents=" + g.ents.size());
        com.xjzb.rts.core.Game.Ent ghost = g.spawn("ghost", 0, s4[0] + 200, s4[1], true);
        float tx = ghost.x + 64, ty = ghost.y;
        g.callNuke(ghost, tx, ty);
        com.xjzb.rts.core.Game.Ent out = g.spawn("marine", 1, tx - 700, ty, true);
        System.out.println("outside at " + out.x + "," + out.y + " hp=" + out.hp);
        for (int i = 0; i < 305; i++) g.update(1f/30f);
        System.out.println("after: outside hp=" + out.hp + " alive=" + out.alive()
            + " ents=" + g.ents.size() + " nukes=" + g.nukes.size());
        for (com.xjzb.rts.core.Game.Ent e : g.ents)
            if (e.team == 1) System.out.println("  team1: " + e.type.key + " at " + (int)e.x + "," + (int)e.y + " hp=" + e.hp);
    }
    static int f(Class<?> c, String n) throws Exception { java.lang.reflect.Field x = c.getDeclaredField(n); x.setAccessible(true); return x.getInt(null); }
    static Object fld(Class<?> c, String n) throws Exception { java.lang.reflect.Field x = c.getDeclaredField(n); x.setAccessible(true); return x.get(null); }
}
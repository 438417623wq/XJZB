public class _Dbg8 {
    public static void main(String[] a) throws Exception {
        Class<?> gd = Class.forName("GameDesktop");
        for (String m : new String[]{"readManifest", "readMap"}) {
            java.lang.reflect.Method x = gd.getDeclaredMethod(m); x.setAccessible(true); x.invoke(null);
        }
        java.lang.reflect.Method cg = gd.getDeclaredMethod("cleanGame", String.class); cg.setAccessible(true);
        com.xjzb.rts.core.Game g = (com.xjzb.rts.core.Game) cg.invoke(null, "terran");
        g.update(1f/30f);
        System.out.println("base cap=" + g.supplyCap + " used=" + g.supplyUsed);
        for (com.xjzb.rts.core.Game.Ent e : g.ents)
            if (e.team == 0 && e.isBuilding() && !e.constructing)
                System.out.println("  bldg " + e.type.key + " supply=" + com.xjzb.rts.core.Game.supplyProvided(e.type.key));
        int before = g.supplyCap;
        g.spawn("depot", 0, 460, 400, true);
        g.update(1f/30f);
        System.out.println("after depot: " + before + " -> " + g.supplyCap + " (delta " + (g.supplyCap-before) + ")");
        g.mineralsPlayer = 5000;
        int t0 = g.supplyCap;
        String why = g.raiseSupplyCap();
        g.update(1f/30f);
        System.out.println("raise: why=" + why + " tier=" + g.capTier + " " + t0 + " -> " + g.supplyCap);
        System.out.println("capTier()=" + g.capTier());
    }
}